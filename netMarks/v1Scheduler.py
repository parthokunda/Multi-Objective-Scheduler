from kubernetes import watch, client, config
import json
import subprocess
import logging as logs
import sqlite3
import random

NET_WEIGHT = .5
CPU_WEIGHT = .5

logs.basicConfig(filename="logscheduler.txt", level=logs.DEBUG, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def run_shell_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Error: {result.stderr.strip()}")
            return None

    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

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
    # only take the running pods on nodes, otherwise descheduled pods might get calculated
    pod_on_node =  run_shell_command(f"kubectl get pods --namespace=default --field-selector spec.nodeName={nodeName} | grep Running | awk '{{print $1}}'").split()
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
    score = 0.0
    netScore = 0.0
    cpuScore = 0.0

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT MAX(total_rate) as max_rate, MIN(total_rate) as min_rate
                    FROM (
                        SELECT SUM(rate) as total_rate,source_app  from netRate GROUP BY source_app
                    ) AS GROUPED_DATA;
                   ''')
    max_net, min_net = cursor.fetchall()[0]
    cursor.execute('''
                   SELECT MAX(total_rate) as max_rate, MIN(total_rate) as min_rate
                    FROM (
                        SELECT SUM(rate) as total_rate,source_app  from cpuRate GROUP BY source_app
                    ) AS GROUPED_DATA;
                   ''')
    max_cpu, min_cpu = cursor.fetchall()[0]

    cursor.execute('''
                    SELECT destination_app, rate from netRate where source_app = ?;
                   ''', (scheduleAppName,))
    netRates = cursor.fetchall()

    cursor.execute('''
                        SELECT source_app, rate from cpuRate;
                   ''')
    cpuRates = cursor.fetchall()

    conn.close()

    for dest_app, rate in netRates:
        if dest_app in appOnNodeList:
            netScore += (rate - min_net) / max_net
    for app_name, cpu in cpuRates:
        if app_name in appOnNodeList :
            cpuScore += (cpu - min_cpu) / max_cpu

    score = - cpuScore * CPU_WEIGHT + netScore * NET_WEIGHT

    logs.info(f'AppName: {scheduleAppName} Node: {node} netScore: {netScore} cpuScore: {cpuScore} score: {score}')

    return score


def v1SchedulerScore(appName):
    nodeList = nodes_available()
    mxScore = -10000000000
    selectedNode = random.choice(nodeList)
    for node in nodeList:
        score = scoreNode(node, appName)
        if mxScore < score:
            mxScore = score
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