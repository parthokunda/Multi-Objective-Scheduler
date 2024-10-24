import os
from concurrent.futures import ThreadPoolExecutor
from kubernetes import client, config, watch
import sqlite3
import logging
from query import queryProm
from time import sleep


logging.basicConfig(filename="testLog.txt", level=logging.DEBUG, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

config.load_kube_config()

v1 = client.CoreV1Api()
w = watch.Watch()

all_app_list = set([
    "adservice", 
    "cartservice", 
    "checkoutservice", 
    "currencyservice", 
    "emailservice", 
    "frontend", 
    "paymentservice", 
    "productcatalogservice", 
    "recommendationservice", 
    "redis-cart", 
    "shippingservice"
])

pods = v1.list_namespaced_pod("default")
app_list = set()
podToApp = {}

def updateRateForQuery(matrix:dict, query:str):
    reply = queryProm(query)
    if reply == None:
        logging.critical("no reply found")
        exit(0)
    
    if 'data' in reply and 'result' in reply['data']:
        for dataPoint in reply['data']['result']:
            source_app = dataPoint['metric']['source_app']
            dest_app = dataPoint['metric']['destination_app']
            if source_app not in all_app_list or dest_app not in all_app_list:
                continue
            value = float(dataPoint['value'][1])
            matrix[source_app][dest_app] += value
    
    return matrix

def updateCPU(matrix:dict, query:str):
    reply = queryProm(query)
    if reply == None:
        logging.critical("no reply found")
        exit(0)
    if 'data' in reply and 'result' in reply['data']:
        for dataPoint in reply['data']['result']:
            pod_name = dataPoint['metric']['pod']
            value = float(dataPoint['value'][1])
            if pod_name in podToApp and podToApp[pod_name] in matrix.keys():
                matrix[podToApp[pod_name]] += value
    return matrix
    

def update():
    print('Thread Started')
    logging.debug('Update Started')
    rate = {}
    cpu = {}
    for app1 in all_app_list:
        rate.update({app1 : {}})
        cpu.update({app1 : float(0)})
        for app2 in all_app_list:
            if app1 != app2:
                rate[app1].update({app2: float(0)})
    
    rate = updateRateForQuery(rate, f'rate(istio_response_bytes_sum{{reporter="source"}}[60s])')
    rate = updateRateForQuery(rate, f'rate(istio_request_bytes_sum{{reporter="source"}}[60s])')
    rate = updateRateForQuery(rate, f'rate(istio_tcp_sent_bytes_total{{reporter="source"}}[60s])')
    rate = updateRateForQuery(rate, f'rate(istio_tcp_received_bytes_total{{reporter="source"}}[60s])')

    cpu = updateCPU(cpu, f'rate (container_cpu_usage_seconds_total{{image="", namespace="default"}}[1m])')
    
    logging.debug(f'Rate after Prom Query: {rate}')
    logging.debug(f'CPU after Prom Query: {cpu}')

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM "netRate";')
    all_rate = cursor.fetchall()
    cursor.execute(f'SELECT * FROM cpuRate')
    all_cpu = cursor.fetchall()
    cpu_insertion = []
    rate_insertion = []
    
    for data in all_rate:
        src, dest, netRate, tf = data
        netRate = (netRate*tf + rate[src][dest]) / (tf+1)
        tf += 1
        rate_insertion.append((src, dest, netRate, tf))  
    cursor.executemany('INSERT INTO netRate (source_app, destination_app, rate, timeframes) VALUES (?, ?,  ?, ?)', rate_insertion)
    
    for data in all_cpu:
        src, cpuRate, tf = data
        cpuRate = (cpu[src] + cpuRate * tf) / (tf+1)
        tf += 1
        cpu_insertion.append((src, cpuRate, tf))
    cursor.executemany('INSERT INTO cpuRate (source_app, rate, timeframes) VALUES (?, ?, ?)', cpu_insertion)
    
    conn.commit()
    conn.close()
    print('Thread Done')
    logging.debug('Update Done')

def runWebLoad(usercount):
    print(f'Web load with {usercount} users')
    os.system(f"locust -f /root/loadTest/locustfile.py -u {usercount} -r 100 -t {LOADTIME}s -H http://$(kubectl get svc | grep frontend | grep Cluster | awk '{{print $3}}'):80 --headless --only-summary")
    print(f'Done Locust File')

MINUTES = 60 # give multiple of three for three user count
TOTALUPDATETIME = MINUTES * 60 + 3 * 60 # seconds the database will take input
LOADTIME = (MINUTES // 3) * 60 # in seconds each load runtime
USERCOUNTS = [50, 1000, 2000]
USERINDEX = 0 
TIMESTAMP = 0

### USAGE -> for paper benchmark. 
### FRESHLY INSTALL MICROSERVICE PODS, ensure RUNNING status (TODO)
### python initDB.py
### set MINUTES and USERCOUNTS and run
### for normal usage, remove MINUTES break, and load generator if needed

if __name__ == "__main__":
    for pod in pods.items:
        if 'app' in pod.metadata.labels:
            app_list.add(pod.metadata.labels['app'])
            podToApp[pod.metadata.name] = pod.metadata.labels['app']
            
    logging.debug(podToApp)

    with ThreadPoolExecutor() as thread_executor:
        while True:
            if(TIMESTAMP == 60 * (USERINDEX+1) + LOADTIME * USERINDEX):
                thread_executor.submit(runWebLoad, USERCOUNTS[USERINDEX])
                USERINDEX += 1
                sleep(5)
            thread_executor.submit(update)
            sleep(60)
            TIMESTAMP += 60
            if(TIMESTAMP > TOTALUPDATETIME):
                break