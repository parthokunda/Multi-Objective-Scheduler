import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def run_shell_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Error: {result.stderr.strip()}")
            return None

    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def run_default_scheduler():
    os.system('kubectl delete -f /root/microservices-demo/release/manifest-extra-resource.yaml')
    time.sleep(15)
    os.system('kubectl apply -f /root/microservices-demo/release/manifest-extra-resource.yaml')
    time.sleep(5)

def run_scheduler():
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
    os.system(f"timeout {WEBLOADTIME + REST_PERIOD * 2 + 10} python3 /root/loadTest/costMonitor.py {locustFile}")

def runCPUusage():
    os.system(f"python3 /root/loadTest/queryCPUusage.py {locustFile} {WEBLOADTIME + REST_PERIOD * 2 + 10}")
    print("CPU Usage saved")

def runWebLoad():
    print(f"Running locust filename {locustFile}")
    os.system(f"locust --csv {locustFile} --csv-full-history --csv-number {locustFile} -u {USERCOUNT} -r 100 -t {WEBLOADTIME}s -H http://$(kubectl get svc | grep frontend | grep Cluster | awk '{{print $3}}'):80 --headless --only-summary")
    print(f'Done Locust File')

servers = ['pc1', 'pc2', 'pc3', 'pc5']
def create_stress():
    print("Creating server load of 2 core cpu")
    for server in servers:
        os.system(f'ssh {server} stress --cpu 2 &')
    time.sleep(5)

def remove_stress():
    print("Removing server cpu load")
    for server in servers:
        os.system(f'ssh {server} sudo pkill -9 stress')

data_start = 115
jobs = [.5]
WEBLOADTIME = 180
USERCOUNT = 300
REST_PERIOD = 15
data = []

if __name__ == "__main__":
    remove_stress()
    create_stress()
    for user in [100, 200, 300]:
        for i, job in enumerate(jobs):
            # cost_weight = 0
            locustFile = data_start
            data_start+=1
            # net_weight = job
            # cpu_weight = 1.0 - job
            # data.append((locustFile, net_weight, cpu_weight, cost_weight))
            USERCOUNT = user

            thread_exec = ThreadPoolExecutor()
            sched = thread_exec.submit(run_default_scheduler)
            time.sleep(60)

            thread_exec.submit(runCostMonitor)
            time.sleep(REST_PERIOD)
            thread_exec.submit(runWebLoad)
            time.sleep(WEBLOADTIME + REST_PERIOD)
            thread_exec.submit(runCPUusage)

            time.sleep(3)
            os.system(f"rm {locustFile}_exceptions.csv {locustFile}_failures.csv {locustFile}_stats.csv")
            # os.system(f"mv *.csv data/")

            print("DONE")
        print(data)
    remove_stress()
