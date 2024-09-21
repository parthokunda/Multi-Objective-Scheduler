import utils
from kubernetes import client, config
import six
from kubernetes.client.exceptions import (
    ApiTypeError,
    ApiValueError
)

config.load_kube_config()
v1 = client.CoreV1Api()

def eventObj_to_totalRequests(eventObj):
    total_CPU = 0
    total_Memory = 0
    for container in eventObj['object'].spec.containers:
        cpu = container.resources.requests['cpu']
        memory = container.resources.requests['memory']
        total_CPU += utils.convertCPUData(cpu)
        total_Memory += utils.convertMemoryData(memory)
    return total_CPU, total_Memory

def get_all_running_pods():
    pods = v1.list_pod_for_all_namespaces().items
    running_pods = [pod for pod in pods if pod.status.phase == "Running"]

    return running_pods

def get_all_running_pods_in_default_namespace():
    pods = get_all_running_pods()
    in_default_namespace = [pod for pod in pods if pod.metadata.namespace == 'default']

    return in_default_namespace

def get_pods(**kwargs):
    local_var_params = locals()

    all_params = [
        'namespace',
        'status',
        'node'
    ]
    for key, val in six.iteritems(local_var_params['kwargs']):
        if key not in all_params:
            raise ApiTypeError(
                "Got an unexpected keyword argument '%s'"
                " to method get_pods" % key
            )
        local_var_params[key] = val
    del local_var_params['kwargs']

    pods = v1.list_pod_for_all_namespaces().items

    if 'namespace' in local_var_params and local_var_params['namespace'] is not None:
        pods = [pod for pod in pods if pod.metadata.namespace == local_var_params['namespace']]
    if 'status' in local_var_params and local_var_params['status'] is not None:
        pods = [pod for pod in pods if pod.status.phase == local_var_params['status']]
    if 'node' in local_var_params and local_var_params['node'] is not None:
        pods = [pod for pod in pods if pod.spec.node_name == local_var_params['node']]
    
    return pods

def are_all_pods_ready(pods):
    for pod in pods:
        for container_status in pod.status.container_statuses:
            if not container_status.ready:
                return False
    return True