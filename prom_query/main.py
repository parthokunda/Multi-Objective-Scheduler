from kubernetes import client,config
from query1 import query

config.load_kube_config()
v1 = client.CoreV1Api()

node_list = list(map(lambda item: item.metadata.name, v1.list_node(watch=False).items))

pods_info = v1.list_namespaced_pod(namespace="default")
container_name = set()
cnt = 0
for pod_info in pods_info.items:
    for container in pod_info.spec.containers:
        cnt+=1
        container_name.add(container.name)

# pod_list = list(map(lambda item: item.metadata.name, v1.list_pod_for_all_namespaces(watch=False).items))
# container_list = list(map(lambda item: item.spec.containers.name, v1.list_pod_for_all_namespaces(watch=False).items))
# container_list = list(map(lambda))



def node_cpu_usage(node_name, time="1m"):
    query(f"sum(rate(node_cpu_seconds_total{{instance=\"{node_name}\", mode!=\"idle\"}}[{time}]))", f'{node_name}_node_cpu_usage')

def node_memory_usage(node_name, time="1m"):
    query(f"rate(node_memory_MemFree_bytes{{instance=\"{node_name}\"}}[{time}])", f"{node_name}_node_memory_rate")

def container_memory_usage(container, time="1m"):
    query(f'container_memory_working_set_bytes{{container=\"{container}\"}}', f'{container}_container_memory_usage')

def container_cpu_usage(containerName, time="1m"):
    query(f'irate(container_cpu_usage_seconds_total{{container="{containerName}"}}[1m])', f'{containerName}_container_cpu_usage')

if __name__ == "__main__":
    for node in node_list:
        node_cpu_usage(node)
        node_memory_usage(node)
    for container in container_name:
        container_memory_usage(container)
        container_cpu_usage(container)

    # query('rate(node_memory_MemFree_bytes{instance="k8s-vm1"}[5m])')
    # query('container_memory_usage_bytes{container="media-frontend"}')
    # query('rate(container_cpu_usage_seconds_total{container="compose-post-service"}[5m])')
    # print(pod_list)
    # query("rate(node_memory_MemFree_bytes{instance=\"k8s-vm1\"}[30s])", "test")
    # query("sum(rate(node_cpu_seconds_total{instance=\"k8s-vm1\", mode!=\"idle\"}[5m]))")
    # container_cpu_usage("compose-post-service")
    # query('irate(container_network_receive_bytes_total{pod="compose-post-service-67b44dc876-6z8bk"}[1m])')
