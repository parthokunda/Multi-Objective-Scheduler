import os, config.config as config, random, json, subprocess, importlib.util
from scoringFunctions import allScoringFunctions

from kubernetes import client, watch
from k8sApi import v1

from mos_logger import mos_logger as mos_log
import node_info


random.seed(107)

def v2SchedulerScore(appName, event):
    nodeList = node_info.get_name_of_worker_nodes()
    nodeList = node_info.filter_nodes_for_scheduling(nodeList, event)
    if len(nodeList) <= 0:
        print("No Schedulable Nodes Found")
        raise Exception

    # for each function a dictionary of (node, score) pairs
    scores = list[dict[str, float]]()
    for scoringFunction in allScoringFunctions.scoringFunctions:
        scoreFromFunc = scoringFunction.function(appName, nodeList)
        scores.append(scoreFromFunc)

    # without below line, scheduler will always choose the first app's node deterministically 
    if(config.SHUFFLE_NODE_FOR_RANDOM_SCHEDULING):
        random.shuffle(nodeList)

    mnScore = 100.0
    for node in nodeList:
        score = 0.0
        assert len(scores) == len(allScoringFunctions.scoringFunctions)

        for i in range(len(scores)):
            ### for test only
            if allScoringFunctions.scoringFunctions[i].weight == None:
                allScoringFunctions.scoringFunctions[i].weight = 1.0
            score += scores[i][node] * allScoringFunctions.scoringFunctions[i].weight
            mos_log.info(f"function name: {allScoringFunctions.scoringFunctions[i].name} score: {scores[i][node]} weight: {allScoringFunctions.scoringFunctions[i].weight}")

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

# def load_weights():
#     global NET_WEIGHT
#     global CPU_WEIGHT
#     global COST_WEIGHT
#     if len(sys.argv) == 4:
#         NET_WEIGHT = float(sys.argv[1])
#         CPU_WEIGHT = float(sys.argv[2])
#         COST_WEIGHT = float(sys.argv[3])
#         return 
#     # only load from file if not 4 args
#     with open('weights.txt', 'r') as weights:
#         NET_WEIGHT = float(weights.readline())
#         CPU_WEIGHT = float(weights.readline())
#         COST_WEIGHT = float(weights.readline())

#     mos_log.debug(f'weights net : {NET_WEIGHT} cpu: {CPU_WEIGHT} cost: {COST_WEIGHT}')
#     print(f'weights net : {NET_WEIGHT} cpu: {CPU_WEIGHT} cost: {COST_WEIGHT}')


# if __name__ == "__main__":
def run_scheduler():
    w = watch.Watch()
    scheduledId = [] # gonna hold the uid inside event, to avoid multiple schedule try of same pod
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == config.SCHEDULER_NAME and event['object'].metadata.uid not in scheduledId:
            try:
                # load_weights()
                if 'app' in event['object'].metadata.labels:
                    nodeSelected = v2SchedulerScore(event['object'].metadata.labels['app'], event)
                    scheduler(event['object'].metadata.name, nodeSelected)
                    scheduledId.append( event['object'].metadata.uid )
                    mos_log.debug("Done Scheduling")
                else:
                    mos_log.warning("Pod without app label cannot be scheduled")
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])

if __name__ == "__main__":
    run_scheduler()