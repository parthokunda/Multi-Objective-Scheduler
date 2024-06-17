from kubernetes import watch, client, config
import pod_info

config.load_kube_config()
v1 = client.CoreV1Api()
w = watch.Watch()

scheduledId = [] # gonna hold the uid inside event, to avoid multiple schedule try of same pod
for event in w.stream(v1.list_namespaced_pod, "default"):
    if event['object'].status.phase == "Pending" and event['object'].metadata.uid not in scheduledId:
        try:
            print(pod_info.eventObj_to_totalRequests(event))
            break
        except client.rest.ApiException as e:
            print('problem')

