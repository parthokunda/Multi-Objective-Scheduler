import subprocess
import json
from mos_logger import mos_logger as mos_log
from kubernetes import client, watch
import sqlite3
import random
from utils import run_shell_command
import sys
import utils
import node_info, pod_info
from k8sApi import v1

NET_WEIGHT = .33
CPU_WEIGHT = .33
COST_WEIGHT = .33
SCHEDULER_DATABASE_DIR = '/root/socialNetwork/loadTesting/data.db'
random.seed(107)
schedulerName = 'netMarksScheduler'

# returns tuples of current pods on nodeName in (appName, podName) format
def getAllAppToPodMappingsOnNode(nodeName):
    app_to_pods = []
    running_pods_in_default_namespace = pod_info.get_pods(node=nodeName, namespace="default", status="Running")
    pod_names = [pod.metadata.name for pod in running_pods_in_default_namespace]

    mos_log.info(f"all pods on node {nodeName} {str(pod_names)}")
    for pod in running_pods_in_default_namespace:
        app = pod_info.get_app_name_from_pod(pod)
        print(app)
        if app == None or len(app) == 0:
            mos_log.critical(f"app name not found for {pod.metadata.name}")
        else:
            app_to_pods.append((app, pod))
            # logs.info(f"appended {app}, {pod} to list_pod")
    return app_to_pods

def getRateFromDB(cursor, scheduleAppName, neighborApp):
    mos_log.info(f"fetching rate from db with {scheduleAppName} {neighborApp}")
    cursor.execute('''
        SELECT SUM(rate) as score
        FROM app_matrix
        WHERE (source_app = ? and destination_app = ?) or (source_app = ? and destination_app = ?)
    ''', (scheduleAppName, neighborApp, neighborApp, scheduleAppName))
    result = cursor.fetchone()[0]
    if result == None:
        mos_log.critical(f'getRateFromDB {scheduleAppName} {neighborApp} result fetch error')
        exit(0)
    return result

def scoreNode(node, scheduleAppName):
    appOnNodeList = getAllAppToPodMappingsOnNode(node)
    appOnNodeList = [i[0] for i in appOnNodeList]
    mos_log.info(f'app on Node list {appOnNodeList}')
    netScore = 0.0
    cpuScore = 0.0

    conn = sqlite3.connect(SCHEDULER_DATABASE_DIR)
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
    mos_log.info(f'{scheduleAppName} on {node} has all_pod_net_sum {netScore}')
    
    for app_name, cpu in cpuRates:
        if app_name in appOnNodeList :
            cpuScore += cpu

    return netScore, cpuScore

# return a normalized version of costing
def nodeCostScore(nodeList) -> dict[str, float]:
    local_nodes, cloud_nodes = utils.get_node_location()
    running_nodes = utils.getRunningNodes()
    costScores : dict[str,float] = {}

    for node in nodeList:
        if node in running_nodes:
            costScores[node] = 0.0
        else:
            if node in local_nodes:
                costScores[node] = 0.5
            elif node in cloud_nodes:
                costScores[node] = 1.0
            else:
                mos_log.error(f"node not found anywhere {node}")
            mos_log.debug(f'{node} has cost: {costScores[node]}')
    
    mx = max(costScores.values()) + .00001
    mn = min(costScores.values()) 
    mos_log.debug(f'Before normalization cost: {costScores}')
    for node in nodeList:
        costScores[node] = (costScores[node] - mn) / (mx - mn)
    mos_log.debug(f'Cost Score Normalized: {costScores}')
    return costScores

def filter_nodes_for_scheduling(nodeList, event):
    filtered_nodes = []
    for node in nodeList:
        free_cpu, free_mem = node_info.remaining_allocatable_resource_in_node(node)
        req_cpu, req_mem = pod_info.eventObj_to_totalRequests(event)
        if(free_cpu > req_cpu and free_mem > req_mem):
            filtered_nodes.append(node)
    #     print(free_cpu, req_cpu)
    #     print(free_mem, req_mem)
    # print(filtered_nodes)
    return filtered_nodes

def v2SchedulerScore(appName, event):
    nodeList = node_info.get_name_of_worker_nodes()
    nodeList = filter_nodes_for_scheduling(nodeList, event)
    if len(nodeList) <= 0:
        print("No Schedulable Nodes Found")
        raise Exception
    costScores = nodeCostScore(nodeList)
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

    mos_log.debug(f'scores retrieved {nodeList} {netScores} {cpuScores}')
    
    mxNet = max(netScores.values()) + .000001
    mnNet = min(netScores.values())
    mxCpu = max(cpuScores.values()) + .000001
    mnCpu = min(cpuScores.values())
    mos_log.debug(f' mxNet {mxNet} mnNet {mnNet} mxCpu {mxCpu} mnCpu {mnCpu}')

    for node in nodeList:
        netScores[node] = (netScores[node] - mnNet) / (mxNet - mnNet)
        cpuScores[node] = (cpuScores[node] - mnCpu) / (mxCpu - mnCpu)
    
    mos_log.info(f'scores net {netScores}')
    mos_log.info(f'scores cpu {cpuScores}')
    mos_log.info(f'scores cost {costScores}')
        
    mnScore = 100.0
    
    # without below line, scheduler will always choose the first app's node deterministically 
    random.shuffle(nodeList)
    
    for node in nodeList:
        score = netScores[node] * NET_WEIGHT + cpuScores[node] * CPU_WEIGHT + costScores[node] * COST_WEIGHT
        mos_log.debug(f'node: {node} score: {score}')
        if mnScore > score:
            mnScore = score
            selectedNode = node
    mos_log.info(f"Scheduled {appName} to {selectedNode}")

    return selectedNode

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    if result.returncode != 0:
        print("Error executing command:", result.stderr)
        return None
    return result.stdout

def scheduler(name, node, namespace="default"):
    print(f"Scheduling {name} to {node}")
    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node)
    meta=client.V1ObjectMeta(name=name)
    body=client.V1Binding(target=target, metadata=meta, api_version="v1", kind="Binding" )
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)

def load_weights():
    global NET_WEIGHT
    global CPU_WEIGHT
    global COST_WEIGHT
    if len(sys.argv) == 4:
        NET_WEIGHT = float(sys.argv[1])
        CPU_WEIGHT = float(sys.argv[2])
        COST_WEIGHT = float(sys.argv[3])
        return 
    # only load from file if not 4 args
    with open('weights.txt', 'r') as weights:
        NET_WEIGHT = float(weights.readline())
        CPU_WEIGHT = float(weights.readline())
        COST_WEIGHT = float(weights.readline())

    mos_log.debug(f'weights net : {NET_WEIGHT} cpu: {CPU_WEIGHT} cost: {COST_WEIGHT}')
    print(f'weights net : {NET_WEIGHT} cpu: {CPU_WEIGHT} cost: {COST_WEIGHT}')


if __name__ == "__main__":
    w = watch.Watch()
    scheduledId = [] # gonna hold the uid inside event, to avoid multiple schedule try of same pod
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == schedulerName and event['object'].metadata.uid not in scheduledId:
            try:
                load_weights()
                if 'app' in event['object'].metadata.labels:
                    nodeSelected = v2SchedulerScore(event['object'].metadata.labels['app'], event)
                    scheduler(event['object'].metadata.name, nodeSelected)
                    scheduledId.append( event['object'].metadata.uid )
                    mos_log.debug("Done Scheduling")
                else:
                    mos_log.warning("Pod without app label cannot be scheduled")
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])

    

