from kubernetes import watch, client, config
import json
import subprocess
import logging 
import sqlite3
import random

logging.basicConfig(filename="logscheduler.txt", level=logging.INFO, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def run_shell_command(command):
    try:
        # Run the shell command and capture its output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        # Check if the command was successful (return code 0)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # If there was an error, print the error message
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
        logging.info(n)
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                if n.metadata.name not in control_nodes:
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

def getAllAppsOnNode(nodeName):
    list_pod = []
    pod_on_node =  run_shell_command(f"kubectl get pods --namespace=default --field-selector spec.nodeName={nodeName} | awk '{{print $1}}'").split()[1:]
    logging.info(f"all pods on node {nodeName} {str(pod_on_node)}")
    for pod in pod_on_node:
        app = run_shell_command(f"kubectl get pod {pod} --namespace=default -o jsonpath='{{.metadata.labels.app}}'")
        if app == None or len(app) == 0:
            logging.warning("No app name found")
        else:
            list_pod.append((app, pod))
        logging.info(f"appended {app}, {pod} to list_pod")
    return list_pod

def getRateFromDB(cursor, scheduleAppName, neighborApp):
    logging.info(f"fetching rate from db with {scheduleAppName} {neighborApp}")
    cursor.execute('''
        SELECT SUM(rate) as score
        FROM app_matrix
        WHERE (source_app = ? and destination_app = ?) or (source_app = ? and destination_app = ?)
    ''', (scheduleAppName, neighborApp, neighborApp, scheduleAppName))
    result = cursor.fetchone()[0]
    if result == None:
        logging.critical(f'getRateFromDB {scheduleAppName} {neighborApp} result fetch error')
        exit(0)
    return result

def scoreNode(node, scheduleAppName):
    appOnNodeList = getAllAppsOnNode(node)
    score = 0
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    for appOnNode in appOnNodeList:
        app, _ = appOnNode
        score += getRateFromDB(cursor, scheduleAppName, app)
    conn.close()
    return score

def netMarksScheduleScore(appName):
    nodeList = nodes_available()
    mxScore = 0.5
    selectedNode = random.choice(nodeList)
    for node in nodeList:
        score = scoreNode(node, appName)
        if mxScore < score:
            mxScore = score
            selectedNode = node
    logging.info(f"Scheduled {appName} to {selectedNode}")
    return selectedNode

def scheduler(name, node, namespace="default"):
    print(f"Scheduling {name} to {node}")
    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node)
    meta=client.V1ObjectMeta(name=name)
    body=client.V1Binding(target=target, metadata=meta, api_version="v1", kind="Binding" )
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)

if __name__ == "__main__":
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == schedulerName:
            try:
                if 'app' in event['object'].metadata.labels:
                    print(event['object'].metadata.labels['app'])
                    nodeSelected = netMarksScheduleScore(event['object'].metadata.labels['app'])
                    scheduler(event['object'].metadata.name, nodeSelected)
                else:
                    logging.warning("Pod without app label cannot be scheduled")
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])