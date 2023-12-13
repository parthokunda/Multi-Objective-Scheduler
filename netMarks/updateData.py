from concurrent.futures import ThreadPoolExecutor
from kubernetes import client, config, watch
import sqlite3
import logging
from query import queryProm
from time import sleep
import os


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
    "loadgenerator", 
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

if __name__ == "__main__":
    for pod in pods.items:
        if 'app' in pod.metadata.labels:
            app_list.add(pod.metadata.labels['app'])
            podToApp[pod.metadata.name] = pod.metadata.labels['app']
            
    logging.debug(podToApp)

    while True:
        with ThreadPoolExecutor() as thread_executor:
            thread_executor.submit(update)
            sleep(60)