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

s = run_command("kubectl get pods | awk 'NR > 1 && tolower($3) == \"outofcpu\" { print $3 }' | wc -l")
print(int(s))