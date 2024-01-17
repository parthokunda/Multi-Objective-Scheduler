from query import queryRange
import logging as logs 
import csv
import sys

logs.basicConfig(filename="logCPUScrapper.txt", level=logs.DEBUG, 
                    filemode='w',
                    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def queryCPUUsage(filename = "cpuUsage.csv", secondsToRun = 600):
    result = queryRange(f'sum(rate(node_cpu_seconds_total{{mode="user"}}[30s])) by (node)', secondsToRun)
    if 'data' in result and 'result' in result['data'] and len(result['data']['result']) > 0:
        datas = result['data']['result']
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

if __name__ == "__main__":
    filename = "cpuUsage.csv"
    if len(sys.argv) == 3:
        filename = str(sys.argv[1]) + '-' + filename
        seconds = int(sys.argv[2])
    queryCPUUsage(filename, seconds)
    