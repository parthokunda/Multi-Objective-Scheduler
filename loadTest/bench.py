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
    os.system(f"python3 /root/netMarks/v1Scheduler.py {net_weight}")
    
def runCostMonitor():
    os.system(f"python3 /root/loadTest/costMonitor.py {locustFile}")

def runCPUusage():
    os.system(f"python3 /root/loadTest/queryCPUusage.py {locustFile}")
    print("CPU Usage saved")

def runWebLoad():
    print(f"Running locust filename {locustFile}")
    os.system(f"locust --csv {locustFile}-v1_load_2500_8m --csv-full-history -u 2500 -r 100 -t 8m -H http://$(kubectl get svc | grep frontend | grep Cluster | awk '{{print $3}}'):80 --headless --only-summary")
    print(f'Done Locust File')

net_weight = 0.25
locustFile = "1"

if __name__ == "__main__":
    thread_exec = ThreadPoolExecutor()
    # sched = thread_exec.submit(run_scheduler)
    # time.sleep(30)


    thread_exec.submit(runCostMonitor)
    time.sleep(60)
    thread_exec.submit(runWebLoad)
    time.sleep(540)
    thread_exec.submit(runCPUusage)


    time.sleep(5)
    print("DONE. Cntrl + C")
