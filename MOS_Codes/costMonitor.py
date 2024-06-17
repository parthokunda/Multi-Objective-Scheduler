from concurrent.futures import ThreadPoolExecutor
from time import sleep
from kubernetes import client, config
import logging as logs
import csv
import sys
logs.basicConfig(filename="logCostMonitor.txt", level=logs.INFO, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')


config.load_kube_config()
v1 = client.CoreV1Api()
totalCost = 0.0
totalTime = 0
RESOLUTION = 10 # in seconds


def get_node_location():
    local_nodes = []
    cloud_nodes = []

    ret = v1.list_node()
    for item in ret.items:
        if 'node-location' in item.metadata.labels:
            node_loc = item.metadata.labels['node-location']
            if node_loc == 'local':
                local_nodes.append(item.metadata.name)
            elif node_loc == 'cloud':
                cloud_nodes.append(item.metadata.name)
    logs.debug(f'local {local_nodes} cloud {cloud_nodes}')

    return local_nodes, cloud_nodes

def getRunningNodes():
    ret = v1.list_namespaced_pod(namespace="default", watch=False)

    running_nodes = set()
    for item in ret.items:
        logs.debug(f'{item.metadata.name} {item.status.phase} {item.spec.node_name}')
        running_nodes.add(item.spec.node_name)
    logs.debug(f'Running nodes {running_nodes}')

    return running_nodes

def calcCost():
    running_nodes = getRunningNodes()
    global totalCost
    global totalTime

    cost = 0.0
    for node in running_nodes:
        if node in local_nodes:
            cost += 0.5 * (RESOLUTION / 60.0)
        elif node in cloud_nodes:
            cost += 1.0 * (RESOLUTION / 60.0)
        else:
            logs.critical(f'{node} not found in local or cloud')
    
    logs.debug(f'cost is {cost}')
    totalCost += cost
    totalTime += RESOLUTION
    csv_writer.writerow((totalTime, (totalCost / totalTime) * 60, totalCost))
    csvfile.flush()
    logs.info(f'Total Cost: {totalCost} at Time: {totalTime} sec')
    logs.info(f'Avg Cost per Minute: {(totalCost / totalTime) * 60}')
    return totalCost

if __name__ == '__main__':
    if len(sys.argv) > 1:
        csvfile = open(str(sys.argv[1]) + "-costMonitor.csv", "w", newline='')
    else:
        csvfile = open("costMonitor.csv", "w", newline='')
    csv_writer = csv.writer(csvfile)
    local_nodes, cloud_nodes = get_node_location()
    csv_writer.writerow(['totalTime', 'avgCost', 'totalCost'])
    csvfile.flush()
    while True:
        with ThreadPoolExecutor() as thread_executor:
            sleep(RESOLUTION)
            thread_executor.submit(calcCost)