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

def run_scheduler():
    os.system(f'kubectl delete -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    os.system(f'kubectl apply -f /root/microservices-demo/release/kubernetes-extra-netMarks.yaml') 
    time.sleep(5)
    os.system(f"timeout 60 python3 /root/netMarks/v2Scheduler.py {net_weight} {cpu_weight} {cost_weight}")
    
def runCostMonitor():
    # total time 600 second. run cost monitor for a bit more
    os.system(f"timeout {WEBLOADTIME + REST_PERIOD * 2 + 10} python3 /root/loadTest/costMonitor.py {locustFile}")

def runCPUusage():
    os.system(f"python3 /root/loadTest/queryCPUusage.py {locustFile}")
    print("CPU Usage saved")

def runWebLoad():
    print(f"Running locust filename {locustFile}")
    os.system(f"locust --csv {locustFile} --csv-full-history --csv-number {locustFile} -u {USERCOUNT} -r 100 -t {WEBLOADTIME}s -H http://$(kubectl get svc | grep frontend | grep Cluster | awk '{{print $3}}'):80 --headless --only-summary")
    print(f'Done Locust File')

jobs = [(48, 0), (49, .125), (50, .25), (51, .375), (52, .5)]
WEBLOADTIME = 180
USERCOUNT = 2500
REST_PERIOD = 15
data = []

if __name__ == "__main__":
    for i, job in enumerate(jobs):
        cost_weight = 0.25
        locustFile = job[0] + 5
        net_weight = job[1] * (1 - cost_weight)
        cpu_weight = (1 - job[1]) * (1 - cost_weight)
        data.append((locustFile, net_weight, cpu_weight, cost_weight))

        thread_exec = ThreadPoolExecutor()
        sched = thread_exec.submit(run_scheduler)
        time.sleep(30)

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
