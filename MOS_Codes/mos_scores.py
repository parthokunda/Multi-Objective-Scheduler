import utils
from mos_logger import logs as mos_log
import pod_info
import sqlite3

LOCAL_NODE_SCORE = 0.5
CLOUD_NODE_SCORE = 1.0
SCHEDULER_DATABASE_DIR = '/root/socialNetwork/loadTesting/data.db'

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

def nonNormalizedCpuAndNetScoreForNode(node, scheduleAppName):
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
    local_nodes, cloud_nodes = utils.get_node_location(mos_log)
    running_nodes = utils.getRunningNodes(mos_log)
    costScores : dict[str,float] = {}

    for node in nodeList:
        if node in running_nodes:
            costScores[node] = 0.0
        else:
            if node in local_nodes:
                costScores[node] = LOCAL_NODE_SCORE
            elif node in cloud_nodes:
                costScores[node] = CLOUD_NODE_SCORE
            else:
                mos_log.error(f"node not found anywhere {node}")
            mos_log.debug(f'{node} has cost: {costScores[node]}')
    
    mx = max(costScores.values()) + .00001
    mn = min(costScores.values()) 

    for node in nodeList:
        costScores[node] = (costScores[node] - mn) / (mx - mn)
    mos_log.debug(f'Cost Score Normalized: {costScores}')
    return costScores

def getCpuScore(appName, nodeList):
    cpuScores = {}
    for node in nodeList:
        _, cpu = nonNormalizedCpuAndNetScoreForNode(node, appName)
        cpuScores[node] = cpu

    mxCpu = max(cpuScores.values()) + .000001
    mnCpu = min(cpuScores.values())

    mos_log.debug(f'mxCpu {mxCpu} mnCpu {mnCpu}')

    for node in nodeList:
        cpuScores[node] = (cpuScores[node] - mnCpu) / (mxCpu - mnCpu)

    mos_log.info(f'scores cpu {cpuScores}')

def getNetScore(appName, nodeList):
    netScores = {} 

    for node in nodeList:
        net, _ = nonNormalizedCpuAndNetScoreForNode(node, appName)
        netScores[node] = net
    sumNet = sum(netScores.values())

    for key in netScores.keys():
        netScores[key] = sumNet - netScores[key]

    mos_log.debug(f'scores retrieved {nodeList} {netScores}')
    
    mxNet = max(netScores.values()) + .000001
    mnNet = min(netScores.values())
    mos_log.debug(f'mxNet {mxNet} mnNet {mnNet}')

    for node in nodeList:
        netScores[node] = (netScores[node] - mnNet) / (mxNet - mnNet)
    
    mos_log.info(f'scores net {netScores}')
