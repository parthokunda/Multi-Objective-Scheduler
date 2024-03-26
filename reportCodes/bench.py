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
                return False
            pod_count += 1

    if pod_count == 0 :
        return False
    return True

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

REST_PERIOD = 10
WEBLOADTIME = 180

def bench_default(start, times = 1):
    file = open(BASEFILENAME,'a')
    data = []
    data_start = start
    for t in range(times):
        for user in [1000]:
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

            print("DONE")
    file.close()


FILENAME = 'entries.txt'
BASEFILENAME = 'entries_baselines.txt'

if __name__ == "__main__":
    remove_stress()
    time.sleep(10)
    bench_default(1001, 3)