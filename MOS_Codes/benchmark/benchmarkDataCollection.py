import os
from config.config import MOS_SCHEDULER_DIR

def runCostMonitor(csv_number, loadTimeForEachOne, restPeriod):
    # run cost monitor for a bit more than total time
    os.system(f"timeout {loadTimeForEachOne + restPeriod * 2 + 10} python3 {MOS_SCHEDULER_DIR}/costMonitor.py {csv_number}")

def runCPUusage(csv_number, loadTimeForEachOne, restPeriod):
    os.system(f"python3 {MOS_SCHEDULER_DIR}/queryCPUusage.py {csv_number} {loadTimeForEachOne + restPeriod * 2 + 10}")
    print("CPU Usage saved")