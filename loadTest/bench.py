import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess

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
    os.system('kubectl delete -f /root/microservices-demo/release/manifest-extra-resource.yaml')
    time.sleep(15)
    os.system('kubectl apply -f /root/microservices-demo/release/manifest-extra-resource.yaml')
    time.sleep(5)

def run_scheduler(net_weight, cpu_weight, cost_weight):
    os.system(f'kubectl delete -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    time.sleep(15)
    os.system(f'kubectl apply -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    time.sleep(5)
    os.system(f"timeout 60 python3 /root/netMarks/v2Scheduler.py {net_weight} {cpu_weight} {cost_weight}")

def run_netMarks_scheduler():
    os.system(f'kubectl delete -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    time.sleep(15)
    os.system(f'kubectl apply -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    time.sleep(5)
    os.system(f"timeout 60 python3 /root/netMarks/v1Scheduler.py 1.0 0") # all net weight, work like netmarks

# uses my-scheduler using kube-scheduler with a NodeResourceFit set to MostAllocated profile
def run_bin_packing_scheduler():
    os.system('kubectl delete -f /root/microservices-demo/release/kubernetes-bin-packing.yaml')
    time.sleep(15)
    os.system('kubectl apply -f /root/microservices-demo/release/kubernetes-bin-packing.yaml')
    time.sleep(5)
    
def runCostMonitor():
    # run cost monitor for a bit more than total time
    os.system(f"timeout {WEBLOADTIME + REST_PERIOD * 2 + 10} python3 /root/loadTest/costMonitor.py {LOCUSTFILE}")

def runCPUusage():
    os.system(f"python3 /root/loadTest/queryCPUusage.py {LOCUSTFILE} {WEBLOADTIME + REST_PERIOD * 2 + 10}")
    print("CPU Usage saved")

def runWebLoad():
    print(f"Running locust filename {LOCUSTFILE}")
    os.system(f"locust --csv {LOCUSTFILE} --csv-full-history --csv-number {LOCUSTFILE} -u {USERCOUNT} -r 100 -t {WEBLOADTIME}s -H http://$(kubectl get svc | grep frontend | grep Cluster | awk '{{print $3}}'):80 --headless --only-summary")
    print(f'Done Locust File')

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
jobs = [0, .25, .5, .75, 1]
WEBLOADTIME = 180
USERCOUNT = 1000
REST_PERIOD = 15
LOCUSTFILE = None

def benchV2():
    data_start = 301
    file = open('entries.txt','a')
    data = []
    remove_stress()
    # create_stress()
    for user in [1000, 50, 2000]:
        for cost in [0, .25, .5, .75, 1]:
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

def bench_default():
    file = open('entries_baselines.txt','a')
    data = []
    data_start = 611
    remove_stress()
    # create_stress()
    for user in [50, 1000, 2000]:
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

def bench_netMarks():
    file = open('entries_baselines.txt','a')
    data = []
    data_start = 711
    remove_stress()
    # create_stress()
    for user in [50, 1000, 2000]:
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
    bench_default()
    bench_netMarks()