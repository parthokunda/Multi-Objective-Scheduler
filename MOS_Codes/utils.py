from k8sApi import v1
import subprocess
from kubernetes import client, config
from mos_logger import mos_logger as mos_log
import config

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

def get_node_location():
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
    mos_log.debug(f'local {local_nodes} cloud {cloud_nodes}')

    return local_nodes, cloud_nodes

def getRunningNodes():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace="default", watch=False)

    running_nodes = set()
    for item in ret.items:
        mos_log.debug(f'{item.metadata.name} {item.status.phase} {item.spec.node_name}')
        running_nodes.add(item.spec.node_name)
    mos_log.debug(f'Running nodes {running_nodes}')

    return running_nodes

def getAllAppNames():
    appList = []
    for appInfo in config.yamlConfig['microService']['appList']:
        appList.append(appInfo['name'])
    return appList

def getPromethusEndpoint() -> tuple[str, str]:
    return getServiceEndpoint('prometheus')

def getServiceEndpoint(svcName: str) -> str:
    all_services = v1.list_service_for_all_namespaces().items
    # all_services = v1.list_namespaced_service('istio-system').items

    count = 0
    ip = None
    port = None

    for svc in all_services:
        if svc.metadata.name == svcName:
            count += 1
            ip = svc.spec.cluster_ip
            if(len(svc.spec.ports) != 1):
                raise Exception(f'{svcName} service do not have exactly one port')
            port = svc.spec.ports[0].port

    if count > 1:
        raise Exception('Multiple Prometheus services found')
    if count == 0:
        raise Exception(f'{svcName} service not found')

    mos_log.info(f'{svcName} service found at {ip}:{port}')
    return str(ip) + ":" + str(port)
