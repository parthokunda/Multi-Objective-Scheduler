import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess

YAML_FILES_DIR = '/root/socialNetwork/deployments'
SCHEDULER_DIR = '/root/socialNetwork/loadTesting'
FILENAME = 'entries.txt'
BASEFILENAME = 'entries_baselines.txt'

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    if result.returncode != 0:
        print("Error executing command:", result.stderr)
        return None
    return result.stdout

def check_pods_deployed():
    output = run_command("kubectl get pods -n default")
    if output is None:
        print("kubectl get pods failed")
        return False

    lines = output.strip().split('\n')
    pod_count = 0
    
    for line in lines[1:]:  # Skip the header line
        columns = line.split()
        if len(columns) > 1:
            ready = columns[1]
            parts = ready.split('/')
            if parts[0] != parts[1]:
                # print(f"Pod {columns[0]} is not fully ready: {ready}")
                return False
            pod_count += 1

    # print("All pods are fully ready.")
    if pod_count == 0 :
        return False
    return True

def run_default_scheduler():
    os.system(f'kubectl delete -f {YAML_FILES_DIR}/socialDefault.yaml')
    time.sleep(5)
    os.system(f'kubectl apply -f {YAML_FILES_DIR}/socialDefault.yaml')
    time.sleep(5)

def run_scheduler(net_weight, cpu_weight, cost_weight):
    os.system(f'kubectl delete -f {YAML_FILES_DIR}/socialNetMarks.yaml') 
    time.sleep(5)
    os.system(f'kubectl apply -f {YAML_FILES_DIR}/socialNetMarks.yaml') 
    time.sleep(5)
    os.system(f"timeout 120 python3 {SCHEDULER_DIR}/v2Scheduler.py {net_weight} {cpu_weight} {cost_weight}")

def run_netMarks_scheduler():
    os.system(f'kubectl delete -f {YAML_FILES_DIR}/socialNetMarks.yaml') 
    time.sleep(5)
    os.system(f'kubectl apply -f {YAML_FILES_DIR}/socialNetMarks.yaml') 
    time.sleep(5)
    os.system(f"timeout 120 python3 {SCHEDULER_DIR}/v1Scheduler.py 1.0 0") # all net weight, work like netmarks

# uses my-scheduler using kube-scheduler with a NodeResourceFit set to MostAllocated profile
def run_bin_packing_scheduler():
    os.system(f'kubectl delete -f {YAML_FILES_DIR}/socialBinPacking.yaml')
    time.sleep(5)
    os.system(f'kubectl apply -f {YAML_FILES_DIR}/socialBinPacking.yaml')
    time.sleep(5)
    
def runCostMonitor():
    # run cost monitor for a bit more than total time
    os.system(f"timeout {WEBLOADTIME + REST_PERIOD * 2 + 10} python3 {SCHEDULER_DIR}/costMonitor.py {LOCUSTFILE}")

def runCPUusage():
    os.system(f"python3 {SCHEDULER_DIR}/queryCPUusage.py {LOCUSTFILE} {WEBLOADTIME + REST_PERIOD * 2 + 10}")
    print("CPU Usage saved")

def runWebLoad():
    print(f"Running locust filename {LOCUSTFILE}")
    os.system(f"locust --csv {LOCUSTFILE} --csv-full-history --csv-number {LOCUSTFILE} -u {USERCOUNT} -r 100 -t {WEBLOADTIME}s -H http://$(kubectl get svc | grep nginx | grep Cluster | awk '{{print $3}}'):8080 --headless --only-summary")
    print(f'Done Locust File')

def init_social_graph():
    pwd = os.getcwd()
    os.chdir('/root/DeathStarBench/socialNetwork')
    os.system('''python3 scripts/init_social_graph.py --graph=socfb-Reed98 --ip=$(kubectl get svc | grep nginx | grep Cluster | awk '{{print $3}}')''')
    os.chdir(pwd)

servers = ['pc1', 'pc2', 'pc3', 'pc5']
def create_stress(): # to make two core cpu from 4
    print("Creating server load of 2 core cpu")
    for server in servers:
        os.system(f'ssh {server} stress --cpu 2 &')
    time.sleep(5)

def remove_stress():
    print("Removing server cpu load")
    for server in servers:
        os.system(f'ssh {server} sudo pkill -9 stress')

# jobs = [.5, .625, .75, .875, 1]
jobs = [0, 0.25, .5, .75, 1]
# jobs = [0.25]
WEBLOADTIME = 180
USERCOUNT = 1000
REST_PERIOD = 15
LOCUSTFILE = None

def benchV2(start, times=1):
    data_start = start
    file = open(FILENAME,'a')
    data = []
    remove_stress()
    create_stress()
    for t in range(times):
        for user in [50]:
            for cost in [0, 0.25, .5]:
                for i, w in enumerate(jobs):
                    global LOCUSTFILE
                    global USERCOUNT
                    LOCUSTFILE = data_start
                    data_start+=1
                    USERCOUNT = user
                    cost_weight = cost
                    net_weight = w * (1 - cost_weight)
                    cpu_weight = (1-w) * (1 - cost_weight)
                    data.append({'fileNum': LOCUSTFILE, 'net_weight': net_weight, 'cpu_weight': cpu_weight, 
                                'cost_weight': cost_weight, 'userCount': USERCOUNT})
                    file.write(str(data[-1]))
                    file.write('\n')
                    file.flush()

                    thread_exec = ThreadPoolExecutor()
                    run_scheduler(net_weight, cpu_weight, cost_weight)
                    time.sleep(5)
                    while check_pods_deployed() != True:
                        time.sleep(3)
                    print('Pods are running')
                    print('The output is: ', check_pods_deployed())
                    init_social_graph()

                    thread_exec.submit(runCostMonitor)
                    time.sleep(REST_PERIOD)
                    thread_exec.submit(runWebLoad)
                    time.sleep(WEBLOADTIME + REST_PERIOD)
                    thread_exec.submit(runCPUusage)

                    time.sleep(30)

                    print("DONE")
    remove_stress()
    file.close()
    print(data)

def bench_default(start, times = 1):
    file = open(BASEFILENAME,'a')
    data = []
    data_start = start
    remove_stress()
    create_stress()
    for t in range(times):
        for user in [50]:
            global LOCUSTFILE
            global USERCOUNT
            LOCUSTFILE = data_start
            data_start+=1
            USERCOUNT = user
            data.append({'fileNum': LOCUSTFILE, 'baseline': 'default', 'user': USERCOUNT})
            file.write(str(data[-1]))
            file.write('\n')
            file.flush()

            thread_exec = ThreadPoolExecutor()
            run_default_scheduler()
            time.sleep(5)
            while check_pods_deployed() != True:
                time.sleep(3)
            print('Pods are running')
            print('The output is: ', check_pods_deployed())
            init_social_graph()

            thread_exec.submit(runCostMonitor)
            time.sleep(REST_PERIOD)
            thread_exec.submit(runWebLoad)
            time.sleep(WEBLOADTIME + REST_PERIOD)
            thread_exec.submit(runCPUusage)

            time.sleep(30)
            # os.system(f"rm {LOCUSTFILE}_exceptions.csv {LOCUSTFILE}_failures.csv {LOCUSTFILE}_stats.csv")
            # os.system(f"mv *.csv data/")

            print("DONE")
    remove_stress()
    file.close()
    print(data)

def bench_netMarks(start, times):
    file = open(BASEFILENAME,'a')
    data = []
    data_start = start
    remove_stress()
    create_stress()
    for t in range(times):
        for user in [50]:
            global LOCUSTFILE
            global USERCOUNT
            LOCUSTFILE = data_start
            data_start+=1
            USERCOUNT = user
            data.append({'fileNum': LOCUSTFILE, 'baseline': 'netmarks', 'user': USERCOUNT})
            file.write(str(data[-1]))
            file.write('\n')
            file.flush()

            thread_exec = ThreadPoolExecutor()
            run_netMarks_scheduler()
            time.sleep(5)
            while check_pods_deployed() != True:
                time.sleep(3)
            print('Pods are running')
            print('The output is: ', check_pods_deployed())
            init_social_graph()

            thread_exec.submit(runCostMonitor)
            time.sleep(REST_PERIOD)
            thread_exec.submit(runWebLoad)
            time.sleep(WEBLOADTIME + REST_PERIOD)
            thread_exec.submit(runCPUusage)

            time.sleep(30)
            # os.system(f"rm {LOCUSTFILE}_exceptions.csv {LOCUSTFILE}_failures.csv {LOCUSTFILE}_stats.csv")
            # os.system(f"mv *.csv data/")

            print("DONE")
    remove_stress()
    file.close()
    print(data)

def bench_binPack(start, times=1):
    file = open(BASEFILENAME,'a')
    data = []
    data_start = start
    remove_stress()
    create_stress()
    for t in range(times):
        for user in [50]:
            global LOCUSTFILE
            global USERCOUNT
            LOCUSTFILE = data_start
            data_start+=1
            USERCOUNT = user
            data.append({'fileNum': LOCUSTFILE, 'baseline': 'binpack', 'user': USERCOUNT})
            file.write(str(data[-1]))
            file.write('\n')
            file.flush()

            thread_exec = ThreadPoolExecutor()
            run_bin_packing_scheduler()
            time.sleep(5)
            while check_pods_deployed() != True:
                time.sleep(3)
            print('Pods are running')
            print('The output is: ', check_pods_deployed())
            init_social_graph()

            thread_exec.submit(runCostMonitor)
            time.sleep(REST_PERIOD)
            thread_exec.submit(runWebLoad)
            time.sleep(WEBLOADTIME + REST_PERIOD)
            thread_exec.submit(runCPUusage)

            time.sleep(30)
            # os.system(f"rm {LOCUSTFILE}_exceptions.csv {LOCUSTFILE}_failures.csv {LOCUSTFILE}_stats.csv")
            # os.system(f"mv *.csv data/")

            print("DONE")
    remove_stress()
    file.close()
    print(data)


if __name__ == "__main__":
    remove_stress()
    create_stress()
    time.sleep(60)
    bench_binPack(3002, 2)
    bench_default(2002, 2)
    bench_netMarks(4002, 2)
    benchV2(201, 2)