"""
This file when imported should do the following
- Create a database file if it does not exist
- Query Prometheus and update the database
"""

import utils, requests, os, sqlite3
from mos_logger import mos_logger as mos_log
from config import yamlConfig
from k8sApi import v1
from concurrent.futures import ThreadPoolExecutor
from kubernetes import config, watch
from time import sleep
from k8sApi import v1

def initDb(cursor, conn, appNames):
        mos_log.info("Creating Database Tables")

        cursor.execute('DROP TABLE IF EXISTS netRate;')
        cursor.execute('DROP TABLE IF EXISTS cpuRate;')
        conn.commit()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS netRate (
                source_app TEXT NOT NULL,
                destination_app TEXT NOT NULL,
                rate REAL NOT NULL,
                timeframes INT NOT NULL,
                UNIQUE(source_app, destination_app) ON CONFLICT REPLACE,
                CHECK (source_app <> destination_app)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpuRate (
                source_app TEXT NOT NULL,
                rate REAL NOT NULL,
                timeframes INT NOT NULL,
                UNIQUE(source_app) ON CONFLICT REPLACE
            )
        ''')
        sample_data = []

        for appsrc in appNames:
            for appdest in appNames:
                if appsrc == appdest:
                    continue
                sample_data.append((appsrc, appdest, 0.0, 0))

        cursor.executemany('INSERT INTO netRate (source_app, destination_app, rate, timeframes) VALUES (?, ?,  ?, ?)', sample_data)

        cpu_init_data = []
        for app in appNames:
            cpu_init_data.append((app, 0.0, 0))

        cursor.executemany('INSERT INTO cpuRate (source_app, rate, timeframes) VALUES (?, ?, ?)', cpu_init_data)
        conn.commit()
        mos_log.info("Database Tables Created")


def queryProm(query: str) :
    prometheusEndpoint = utils.getPromethusEndpoint()
    url = f'http://{prometheusEndpoint}/api/v1/query'
    params = {
        'query': f'{query}'
    }

    response = requests.get(url, params)
    if response.status_code == 200 :
        return response.json()
    else:
        raise Exception(f'Error in query: {query} response: {response}')

def updateRateForQuery(matrix:dict, query:str):
    reply = queryProm(query)
    if reply == None:
        mos_log.critical("no reply found")
        exit(0)
    
    if 'data' in reply and 'result' in reply['data']:
        for dataPoint in reply['data']['result']:
            source_app = dataPoint['metric']['source_app']
            dest_app = dataPoint['metric']['destination_app']
            # all 3 reviews have same app name. use workload parameter to include v1. istio adds that workload for some reason
            if source_app == "reviews":
                source_app = dataPoint['metric']['source_workload']
            if dest_app == "reviews":
                dest_app = dataPoint['metric']['destination_workload']

            if source_app not in all_app_list or dest_app not in all_app_list:
                continue
            value = float(dataPoint['value'][1])
            matrix[source_app][dest_app] += value
    
    return matrix

def updateCPU(matrix:dict, query:str):
    reply = queryProm(query)
    if reply == None:
        mos_log.critical("no reply found")
        exit(0)
    if 'data' in reply and 'result' in reply['data']:
        for dataPoint in reply['data']['result']:
            pod_name = dataPoint['metric']['pod']
            value = float(dataPoint['value'][1])
            if pod_name in podToApp and podToApp[pod_name] in matrix.keys():
                matrix[podToApp[pod_name]] += value
    return matrix

def update(dbPath):
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    print('Database Information Update Started')
    mos_log.info('Database Information Update Started')
    cursor.execute(f'SELECT * FROM "netRate";')
    test = cursor.fetchall()

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
    
    mos_log.debug(f'Rate after Prom Query: {rate}')
    mos_log.debug(f'CPU after Prom Query: {cpu}')

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
    print('Database Information Update Done')
    mos_log.debug('Database Information Update Done')

def runWebLoad(usercount, locustFile, loadtime, endpoint: str):
    print(f'Web load with {usercount} users')
    os.system(f"locust -f {locustFile} -u {usercount} -r 100 -t {loadtime}s -H http://{endpoint} --headless --only-summary")
    print(f'Done Locust File')

### this block should run when the file is imported
print("Setting up the database")
appNames = utils.getAllAppNames()

shouldInitDb = yamlConfig['database']['shouldInitDb']
shouldCollectData = yamlConfig['dataCollection']['shouldCollectData']
locustFileLocation = yamlConfig['locustFileLocation']
dbPath = yamlConfig['database']['location']

if(shouldInitDb and not shouldCollectData):
    raise Exception("Data collection should be enabled to initialize the database")

if not dbPath.endswith(".db"):
    raise Exception("Database path should end with .db")

if shouldCollectData:
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()

    if shouldInitDb:
        initDb(cursor=cursor, conn=conn, appNames=appNames)

    all_app_list = set(utils.getAllAppNames())

    pods = v1.list_namespaced_pod("default")
    app_list = set()
    podToApp = {}

    for pod in pods.items:
        if 'app' in pod.metadata.labels:
            app_list.add(pod.metadata.labels['serviceName'])
            podToApp[pod.metadata.name] = pod.metadata.labels['serviceName']
            
    mos_log.debug(podToApp)

    MINUTES = yamlConfig['dataCollection']['minute']
    USERCOUNTS = yamlConfig['dataCollection']['userCounts']
    svcToSendLoadName = yamlConfig['svcToSendLoad']
    svcToSendLoadEndpoint = utils.getServiceEndpoint(svcToSendLoadName)

    # each user count will run for MINUTES and 1 minute rest
    totalUpdateTime = MINUTES * 60 + len(USERCOUNTS) * 60 # seconds the database will take input
    singleLoadTime = (MINUTES // len(USERCOUNTS)) * 60 # in seconds each load runtime
    USERINDEX = 0
    timestamp = 0

    # update(conn, cursor, 6996)
    print(f"Getting the data by running web load for {totalUpdateTime} seconds")
    with ThreadPoolExecutor() as thread_executor:
        while True:
            if(timestamp == 60 * (USERINDEX+1) + singleLoadTime * USERINDEX):
                thread_executor.submit(runWebLoad, USERCOUNTS[USERINDEX], locustFileLocation, singleLoadTime, svcToSendLoadEndpoint)
                USERINDEX += 1

            if timestamp == 0:
                sleep(60) # wait for the load to start

            thread_executor.submit(update, dbPath) # we cannot pass conn and cursor to another thread because it is not thread safe
            sleep(60)
            timestamp += 60

            if(timestamp > totalUpdateTime):
                break

    conn.close()
    print(f"Data collection done for {totalUpdateTime} seconds")