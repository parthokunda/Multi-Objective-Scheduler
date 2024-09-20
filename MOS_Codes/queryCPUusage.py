import logging as logs 
import csv
import sys
import requests
import subprocess
from datetime import datetime, timedelta

logs.basicConfig(filename="logCPUScrapper.txt", level=logs.DEBUG, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def run_shell_command(command):
    try:
        # Run the shell command and capture its output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        # Check if the command was successful (return code 0)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # If there was an error, print the error message
            print(f"Error: {result.stderr.strip()}")
            return None

    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def queryCPUUsage(filename = "cpuUsage.csv", secondsToRun = 600):
    result = queryRange(f'sum(rate(node_cpu_seconds_total{{mode="user"}}[30s])) by (node)', secondsToRun)
    if 'data' in result and 'result' in result['data'] and len(result['data']['result']) > 0:
        datas = result['data']['result']
        logs.debug(datas)
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["node_name","timestamp", 'value'])
            for data in datas:
                nodename = data['metric']['node']
                for time,usage in data['values']:
                    csv_writer.writerow((nodename, time, usage))
        print(f"Values successfully saved to cpuUsage.csv")
    else:
        print(result)

def queryRange(query, secondsCount = 600):
    ip = run_shell_command("kubectl  get svc -A | grep prometheus | grep 9090 | awk '{print $4 \":\" $6}'")
    ip = ip.split('/')[0]
    url = f"http://{ip}/api/v1/query_range"

    params = {
        'query': query,
        'start': (datetime.utcnow() - timedelta(seconds=secondsCount)).timestamp(),
        'end': (datetime.utcnow()).timestamp(),
        'step': '15s'
    }

    response = requests.get(url, params)
    if response.status_code == 200 :
        return response.json()
    else:
        print('error in query '+query)
        return None
if __name__ == "__main__":
    filename = "cpuUsage.csv"
    if len(sys.argv) == 3:
        filename = str(sys.argv[1]) + '-' + filename
        seconds = int(sys.argv[2])
    queryCPUUsage(filename, seconds)
    