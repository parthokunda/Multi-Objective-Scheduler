import subprocess
from kubernetes import client, config

def convertCPUData(allocatable_cpu):
    # Convert CPU to millicores (if necessary)
    if 'm' in allocatable_cpu:
        allocatable_cpu = int(allocatable_cpu[:-1])
    else:
        allocatable_cpu = int(allocatable_cpu) * 1000
    return allocatable_cpu

def convertMemoryData(memory):
    if 'Mi' in memory:
        memory = int(memory[:-2])
    elif 'Gi' in memory:
        memory = int(memory[:-2]) * 1024
    return memory

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

def get_node_location(logs):
    config.load_kube_config()
    v1 = client.CoreV1Api()
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

def getRunningNodes(logs):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace="default", watch=False)

    running_nodes = set()
    for item in ret.items:
        logs.debug(f'{item.metadata.name} {item.status.phase} {item.spec.node_name}')
        running_nodes.add(item.spec.node_name)
    logs.debug(f'Running nodes {running_nodes}')

    return running_nodes
