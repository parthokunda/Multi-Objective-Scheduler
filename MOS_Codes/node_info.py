from kubernetes import client, config
from utils import convertCPUData, convertMemoryData

config.load_kube_config()
v1 = client.CoreV1Api()


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

def remaining_allocatable_resource(node_name):
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
