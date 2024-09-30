from kubernetes import client, config
from utils import convertCPUData, convertMemoryData
from mos_logger import mos_logger as mos_log
import pod_info
from k8sApi import v1

def get_total_requested_resources(node_name):
    pods = v1.list_pod_for_all_namespaces(watch=False)
    total_cpu = 0
    total_memory = 0

    for pod in pods.items:
        if pod.spec.node_name == node_name:
            for container in pod.spec.containers:
                if container.resources.requests:
                    if 'cpu' in container.resources.requests:
                        cpu_request = container.resources.requests['cpu']
                        total_cpu += convertCPUData(cpu_request)
                    if 'memory' in container.resources.requests:
                        memory_request = container.resources.requests['memory']
                        total_memory += convertMemoryData(memory_request)

    return total_cpu, total_memory

def remaining_allocatable_resource_in_node(node_name):
    node = v1.read_node(name=node_name)
    allocatable = node.status.allocatable

    allocatable_cpu = allocatable['cpu']
    allocatable_memory = allocatable['memory']

    # Convert CPU to millicores (if necessary)
    if 'm' in allocatable_cpu:
        allocatable_cpu = int(allocatable_cpu[:-1])
    else:
        allocatable_cpu = int(allocatable_cpu) * 1000

    # Convert memory to MiB (if necessary)
    if 'Ki' in allocatable_memory:
        allocatable_memory = int(allocatable_memory[:-2]) / 1024
    elif 'Mi' in allocatable_memory:
        allocatable_memory = int(allocatable_memory[:-2])
    elif 'Gi' in allocatable_memory:
        allocatable_memory = int(allocatable_memory[:-2]) * 1024

    used_cpu, used_memory = get_total_requested_resources(node_name=node_name)
    return allocatable_cpu-used_cpu, allocatable_memory-used_memory

def get_name_of_control_nodes():
    control_nodes = v1.list_node(limit = 4, label_selector='node-role.kubernetes.io/control-plane=').items
    control_node_names = [node.metadata.name for node in control_nodes]
    return control_node_names

def get_name_of_worker_nodes():
    control_node_names = get_name_of_control_nodes()

    ready_nodes = []
    for node in v1.list_node().items:
        for status in node.status.conditions:
            if status.status == "True" and status.type == "Ready":
                if node.metadata.name not in control_node_names:
                    ready_nodes.append(node.metadata.name)
    return ready_nodes

def filter_nodes_for_scheduling(nodeList, event):
    filtered_nodes = []
    for node in nodeList:
        free_cpu, free_mem = remaining_allocatable_resource_in_node(node)
        req_cpu, req_mem = pod_info.eventObj_to_totalRequests(event)
        if(free_cpu > req_cpu and free_mem > req_mem):
            filtered_nodes.append(node)
    return filtered_nodes