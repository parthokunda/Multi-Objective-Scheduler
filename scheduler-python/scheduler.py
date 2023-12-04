from kubernetes import watch, client, config
import json

config.load_kube_config()
v1 = client.CoreV1Api()
schedulerName = "pysched"

vertical_align = {
    "nginx-thrift": 0,
    "media-frontend": 0,
    "media-service" : 1,
    "unique-id-service" : 1,
    "home-timeline-service" : 1,
    "user-mention-service" : 1,
    "user-timeline-service" : 1,
    "jaeger" : 1,
    "text-service" : 1,
    "user-service" : 1,
    "post-storage-service" : 1,
    "social-graph-service" : 1,
    "url-shorten-service" : 1,
    "compose-post-service" : 1,
    "user-timeline-redis" : 2,
    "home-timeline-redis" : 2,
    "social-graph-redis" : 2,
    "url-shorten-memcached" : 2,
    "user-memcached" : 2,
    "media-memcached" : 2,
    "post-storage-memcached" : 2,
    "url-shorten-mongodb" : 2,
    "social-graph-mongodb" : 2,
    "user-mongodb" : 2,
    "user-timeline-mongodb" : 2,
    "media-mongodb" : 2,
    "post-storage-mongodb" : 2,
}

def container_process():
    pods_info = v1.list_namespaced_pod(namespace="default")
    container_name = set()
    cnt = 0
    for pod_info in pods_info.items:
        for container in pod_info.spec.containers:
            cnt+=1
            container_name.add(container.name)
    return container_name

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

def scheduler(name, node, namespace="default"):
    print(f"Scheduling {name} to {node}")
    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node)
    meta=client.V1ObjectMeta(name=name)
    body=client.V1Binding(target=target, metadata=meta, api_version="v1", kind="Binding" )
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)

def vertical_scheduler(containername, podname, nodeList):
    if containername in vertical_align:
        scheduler(podname, nodeList[vertical_align[containername]])
    else:
        print(f'{containername} not found')

def main():
    nodeList = nodes_available()
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == schedulerName:
            try:
                vertical_scheduler(event['object'].spec.containers[0].name, event['object'].metadata.name, nodeList)

                # print("Need scheduling for image: ", event['object'].metadata.name)
                # print ("Scheduling " + event['object'].metadata.name)
                res = scheduler(event['object'].metadata.name, nodes_available()[1])
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])


if __name__ == "__main__":
    main()