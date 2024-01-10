from kubernetes import watch, client, config
import json
import logging as logs
import sqlite3
import random
from utils import run_shell_command
import sys

NET_WEIGHT = .25
CPU_WEIGHT = 1.0 - NET_WEIGHT
random.seed(107)

logs.basicConfig(filename="logscheduler.txt", level=logs.DEBUG, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

config.load_kube_config()
v1 = client.CoreV1Api()

schedulerName = 'netMarksScheduler'

def nodes_available():
    control_nodes = run_shell_command("kubectl get nodes --selector=node-role.kubernetes.io/control-plane="" | awk '{print $1}'").split()[1:]
    ready_nodes = []
    for n in v1.list_node().items:
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                if n.metadata.name not in control_nodes:
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

# returns tuples of current pods on nodeName in (appName, podName) format 
def getAllAppsOnNode(nodeName):
    list_pod = []
    #? not done(grep RUNNING problemous) only take the running pods on nodes, otherwise descheduled pods might get calculated
    pod_on_node =  run_shell_command(f"kubectl get pods --namespace=default --field-selector spec.nodeName={nodeName} | awk '{{print $1}}'").split()[1:]
    logs.info(f"all pods on node {nodeName} {str(pod_on_node)}")
    for pod in pod_on_node:
        app = run_shell_command(f"kubectl get pod {pod} --namespace=default -o jsonpath='{{.metadata.labels.app}}'")
        if app == None or len(app) == 0:
            logs.warning("No app name found")
        else:
            list_pod.append((app, pod))
            logs.info(f"appended {app}, {pod} to list_pod")
    return list_pod

def getRateFromDB(cursor, scheduleAppName, neighborApp):
    logs.info(f"fetching rate from db with {scheduleAppName} {neighborApp}")
    cursor.execute('''
        SELECT SUM(rate) as score
        FROM app_matrix
        WHERE (source_app = ? and destination_app = ?) or (source_app = ? and destination_app = ?)
    ''', (scheduleAppName, neighborApp, neighborApp, scheduleAppName))
    result = cursor.fetchone()[0]
    if result == None:
        logs.critical(f'getRateFromDB {scheduleAppName} {neighborApp} result fetch error')
        exit(0)
    return result

def scoreNode(node, scheduleAppName):
    appOnNodeList = getAllAppsOnNode(node)
    appOnNodeList = [i[0] for i in appOnNodeList]
    logs.info(f'app on Node list {appOnNodeList}')
    netScore = 0.0
    cpuScore = 0.0

    conn = sqlite3.connect('/root/netMarks/data.db')
    cursor = conn.cursor()

    cursor.execute('''
                    SELECT source_app,destination_app, rate from netRate where source_app = ? or destination_app = ?;
                   ''', (scheduleAppName,scheduleAppName))
    netRates = cursor.fetchall()

    cursor.execute('''
                        SELECT source_app, rate from cpuRate;
                   ''')
    cpuRates = cursor.fetchall()

    conn.close()

    for src_app, dest_app, rate in netRates:
        if dest_app in appOnNodeList or src_app in appOnNodeList:
            netScore += rate
    logs.debug(f'{scheduleAppName} on {node} has all_pod_net_sum {netScore}')
    
    for app_name, cpu in cpuRates:
        if app_name in appOnNodeList :
            cpuScore += cpu

    return netScore, cpuScore


def v1SchedulerScore(appName):
    nodeList = nodes_available()
    netScores = {} 
    cpuScores = {}

    for node in nodeList:
        net, cpu = scoreNode(node, appName)
        # scores.append((node, net, cpu))
        netScores[node] = net
        cpuScores[node] = cpu
    
    sumNet = sum(netScores.values())
    for key in netScores.keys():
        netScores[key] = sumNet - netScores[key]

    logs.debug(f'scores retrieved {nodeList} {netScores} {cpuScores}')
    
    mxNet = max(netScores.values()) + .000001
    mnNet = min(netScores.values())
    mxCpu = max(cpuScores.values()) + .000001
    mnCpu = min(cpuScores.values())
    logs.debug(f' mxNet {mxNet} mnNet {mnNet} mxCpu {mxCpu} mnCpu {mnCpu}')

    for node in nodeList:
        netScores[node] = (netScores[node] - mnNet) / (mxNet - mnNet)
        cpuScores[node] = (cpuScores[node] - mnCpu) / (mxCpu - mnCpu)
    
    logs.info(f'scores after normalization {netScores} {cpuScores}')
        
    mnScore = 100.0
    
    # without below line, scheduler will always choose the first app's node deterministically 
    random.shuffle(nodeList)
    
    for node in nodeList:
        score = netScores[node] * NET_WEIGHT + cpuScores[node] * CPU_WEIGHT
        logs.debug(f'node: {node} score: {score}')
        if mnScore > score:
            mnScore = score
            selectedNode = node
    logs.info(f"Scheduled {appName} to {selectedNode}")

    return selectedNode

def scheduler(name, node, namespace="default"):
    print(f"Scheduling {name} to {node}")
    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node)
    meta=client.V1ObjectMeta(name=name)
    body=client.V1Binding(target=target, metadata=meta, api_version="v1", kind="Binding" )
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        NET_WEIGHT = float(sys.argv[1])
        CPU_WEIGHT = float(sys.argv[2])
    
    logs.debug(f'net weight : {NET_WEIGHT}')
    print(f"Scheduler with net weight = {NET_WEIGHT} cpu weight = {CPU_WEIGHT}")
    w = watch.Watch()
    scheduledId = [] # gonna hold the uid inside event, to avoid multiple schedule try of same pod
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == schedulerName and event['object'].metadata.uid not in scheduledId:
            try:
                if 'app' in event['object'].metadata.labels:
                    nodeSelected = v1SchedulerScore(event['object'].metadata.labels['app'])
                    scheduler(event['object'].metadata.name, nodeSelected)
                    scheduledId.append( event['object'].metadata.uid )
                    logs.debug("Done Scheduling")
                else:
                    logs.warning("Pod without app label cannot be scheduled")
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])
