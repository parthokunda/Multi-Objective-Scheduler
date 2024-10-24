import os, config.config as config, random, json, subprocess, importlib.util
from scoringFunctions import allScoringFunctions
from concurrent.futures import ThreadPoolExecutor

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

def scheduler(name, node, namespace="default"):
    print(f"Scheduling {name} to {node}")
    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node)
    meta=client.V1ObjectMeta(name=name)
    body=client.V1Binding(target=target, metadata=meta, api_version="v1", kind="Binding" )
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)


# def scheduleInThread(event):
#     try:
#         nodeSelected = v2SchedulerScore(event['object'].metadata.labels['app'], event)
#         scheduler(event['object'].metadata.name, nodeSelected)
#         mos_log.debug("Done Scheduling")
#     except client.rest.ApiException as e:
#         print(json.loads(e.body)['message'])
#     except Exception as e:
#         mos_log.error(f"Error in scheduling: {str(e)}")

# if __name__ == "__main__":
def run_scheduler():
    w = watch.Watch()
    # threadExec = ThreadPoolExecutor()

    scheduledId = [] # gonna hold the uid inside event, to avoid multiple schedule try of same pod

    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == config.SCHEDULER_NAME and event['object'].metadata.uid not in scheduledId:
            try:
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