from concurrent.futures import ThreadPoolExecutor
from kubernetes import client, config, watch
import sqlite3
import logging
from query import queryProm
from time import sleep
import os

os.system("$pwd;rm logData.txt")
logging.basicConfig(filename="logData.txt", level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
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

def getReqRate(app1, app2):
    rate = 0
    reply1 = queryProm(f'rate(istio_request_bytes_sum{{source_app="{app1}", destination_app="{app2}", reporter="source"}}[60s])')
    reply2 = queryProm(f'rate(istio_tcp_sent_bytes_total{{source_app="{app1}", destination_app="{app2}", reporter="source"}}[60s])')
    if reply1 == None:
        logging.critical("no reply found")
        print('no reply')
        exit(0)
    if 'data' in reply1 and 'result' in reply1['data']:
        valid_data_cnt = 0
        for dataPoint in reply1['data']['result']:
            if 'response_code' in dataPoint['metric'] and dataPoint['metric']['response_code'] == '200':
                logging.debug("inside data addition")
                valid_data_cnt += 1
                logging.debug(f'{valid_data_cnt} with data {dataPoint["value"][1]}')
                rate += float(dataPoint['value'][1])
                logging.debug(f'addition done')
    if reply2 == None:
        logging.critical("no reply found")
        print('no reply')
        exit(0)
    if 'data' in reply2 and 'result' in reply2['data']:
        valid_data_cnt = 0
        for dataPoint in reply2['data']['result']:
            rate += float(dataPoint['value'][1])
            tcp = float(dataPoint['value'][1])
            logging.info(f'tcp sent rate {tcp}')
    logging.info(f'request rate between {app1} and {app2} is ' + str(rate))
    return float(rate)

def getResRate(app1, app2):
    rate = 0
    reply1 = queryProm(f'rate(istio_response_bytes_sum{{source_app="{app1}", destination_app="{app2}", reporter="source"}}[60s])')
    reply2 = queryProm(f'rate(istio_tcp_received_bytes_total{{source_app="{app1}", destination_app="{app2}", reporter="source"}}[60s])')
    if reply1 == None:
        logging.critical("no reply found")
        print('no reply')
        exit(0)
    if 'data' in reply1 and 'result' in reply1['data']:
        valid_data_cnt = 0
        for dataPoint in reply1['data']['result']:
            if 'response_code' in dataPoint['metric'] and dataPoint['metric']['response_code'] == '200':
                valid_data_cnt += 1
                rate += float(dataPoint['value'][1])

    if reply2 == None:
        logging.critical("no reply found")
        print('no reply')
        exit(0)
    if 'data' in reply2 and 'result' in reply2['data']:
        valid_data_cnt = 0
        for dataPoint in reply2['data']['result']:
            rate += float(dataPoint['value'][1])
            tcp = float(dataPoint['value'][1])
            logging.info(f'tcp received rate {tcp}')
    
    logging.info(f'Response rate between {app1} and {app2} is ' + str(rate))
    return float(rate)

for pod in pods.items:
    if 'app' in pod.metadata.labels:
        app_list.add(pod.metadata.labels['app'])

def getRateTfFromDB(cursor, appsrc, appdest):
    cursor.execute(f'SELECT * FROM "app_matrix" where source_app="{appsrc}" and destination_app="{appdest}";')
    row = cursor.fetchall()
    if len(row) > 1:
        logging.critical(f"more than one row somehow")
        print("More than one row")
        exit(0)
    _,_,rateDB,tf = row[0]
    return rateDB, tf

def updateRate():
    print("Thread Started")
    conn = sqlite3.connect('data.db')
    logging.info(f'Updating Data in DB')
    cursor = conn.cursor()
    for app1 in app_list:
        for app2 in app_list:
            if app1 == app2:
                continue
            rate = getReqRate(app1,app2) + getResRate(app1,app2)
            if(rate > 0):
                print(rate, app1, app2)
            rateDB, tf = getRateTfFromDB(cursor, app1, app2)
            rateDB = (rateDB * tf + rate) / (tf+1)
            tf += 1
            logging.info(f'Inserting data {app1} {app2} {str(rateDB)} {str(tf)}')
            cursor.execute(f'INSERT INTO app_matrix (source_app, destination_app, rate, timeframes) VALUES (?, ?, ?, ?)', (app1, app2, rateDB, tf))
            conn.commit()
    conn.close()
    print("Thread Done")
        
print("Updater Running")

while True:
    with ThreadPoolExecutor() as thread_executor:
        thread_executor.submit(updateRate)
        sleep(60)
# updateRate()
        
# def updateDataForApp(appName):
#     queryProm('istio_request_bytes_sum{source_app="frontend", destination_app="cartservice", reporter="source"}')
        
# for event in w.stream(v1.list_pod_for_all_namespaces):
#     if event['object'].metadata.namespace != 'default':
#         continue
#     if(event['type'] == "DELETED"):
#         if 'app' in event['object'].metadata.labels:
#             print(str(event['object'].metadata.labels['app']) + " deleted")
#             updateDataForApp(event['object'].metadata.labels['app'])

    # if event['type'] == "ADDED":
    #     if 'app' in event['object'].metadata.labels:
    #         print(event['object'].metadata.labels['app'])
