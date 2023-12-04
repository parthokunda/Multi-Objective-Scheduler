import requests
import csv
from datetime import datetime, timedelta

link = "10.98.206.32:9090"

def getListPods():
    podList = []
    url = f"http://{link}/api/v1/query"
    params = {
        'query' : "kube_pod_info"
    }

    response = requests.get(url, params)
    if response.status_code == 200:
        json_data = response.json()
        values = json_data['data']['result']
        print(len(values))
        for entry in values:
            if(entry['value'][1] == '1'):
                podList.append(entry['metric']['pod'])
    return podList


def query(query, csvFileName="test"):
    url = f"http://{link}/api/v1/query_range"

    params = {
        'query': query,
        'start': (datetime.utcnow() - timedelta(minutes=30)).timestamp(),
        'end': (datetime.utcnow()).timestamp(),
        'step': '1m'
    }
    # print((datetime.utcnow() - timedelta(hours=1)).timestamp())
    # print( datetime.utcnow().timestamp())

    response = requests.get(url, params=params)

    if response.status_code == 200:
        json_data = response.json()
        # print(json_data)
        if 'data' in json_data and 'result' in json_data['data'] and len(json_data['data']['result']) > 0:

            values = json_data['data']['result'][0]['values']

            with open(csvFileName+".csv", 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                csv_writer.writerow(["timestamp", 'value'])

                for value in values:
                    csv_writer.writerow(value)
            
            print(f"Values successfully saved to {query}.csv")
        else:
            print(json_data)
            print("No data found for "+query)
    else:
        print(f"Error: Unable to retrieve data. Status code: {response.status_code}")

# os.system("rm *.csv")
# query('container_memory_usage_bytes{container="media-frontend"}')
# query('rate(node_memory_MemFree_bytes{instance="k8s-vm1"}[5m])')
# query('rate(container_cpu_usage_seconds_total{container="compose-post-service"}[5m])')
# podList = getListPods()
# for podname in podList:
#     print('container_memory_usage_bytes{pod="'+podname+'"}')
#     query('rate(container_network_transmit_bytes_total{pod='+podname+'}[5m])+rate(container_network_receive_bytes_total{pod='+podname+'}[5m])')
# query('rate(container_network_transmit_bytes_total{pod="compose-post-service-67b44dc876-96vvx"}[5m])+rate(container_network_receive_bytes_total{pod="compose-post-service-67b44dc876-96vvx"}[5m])')
