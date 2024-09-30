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
import mos_scores

NET_WEIGHT = .33
CPU_WEIGHT = .33
COST_WEIGHT = .33
mos_scores.SCHEDULER_DATABASE_DIR = '/root/socialNetwork/loadTesting/data.db'
SHUFFLE_NODE_FOR_RANDOM_SCHEDULING = True

random.seed(107)
schedulerName = 'netMarksScheduler'


# def getRateFromDB(cursor, scheduleAppName, neighborApp):
#     mos_log.info(f"fetching rate from db with {scheduleAppName} {neighborApp}")
#     cursor.execute('''
#         SELECT SUM(rate) as score
#         FROM app_matrix
#         WHERE (source_app = ? and destination_app = ?) or (source_app = ? and destination_app = ?)
#     ''', (scheduleAppName, neighborApp, neighborApp, scheduleAppName))
#     result = cursor.fetchone()[0]
#     if result == None:
#         mos_log.critical(f'getRateFromDB {scheduleAppName} {neighborApp} result fetch error')
#         exit(0)
#     return result


def v2SchedulerScore(appName, event):
    nodeList = node_info.get_name_of_worker_nodes()
    nodeList = node_info.filter_nodes_for_scheduling(nodeList, event)
    if len(nodeList) <= 0:
        print("No Schedulable Nodes Found")
        raise Exception

    costScores = mos_scores.getCostScoresForNode(nodeList)
    netScores  = mos_scores.getNetScore(appName, nodeList)
    cpuScores  = mos_scores.getCpuScore(appName, nodeList)

    # without below line, scheduler will always choose the first app's node deterministically 
    if(SHUFFLE_NODE_FOR_RANDOM_SCHEDULING):
        random.shuffle(nodeList)

    mnScore = 100.0
    for node in nodeList:
        score = netScores[node] * NET_WEIGHT + cpuScores[node] * CPU_WEIGHT + costScores[node] * COST_WEIGHT
        mos_log.debug(f'node: {node} score: {score}')
        if mnScore > score:
            mnScore = score
            selectedNode = node

    mos_log.info(f"Scheduling {appName} to {selectedNode}")
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

    

