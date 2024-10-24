import csv, sys, os, time
import utils, pod_info
from scoringFunctions import allScoringFunctions
from concurrent.futures import ThreadPoolExecutor

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import yamlConfig, MOS_SCHEDULER_DIR
import benchmark.benchmarkDataCollection as benchmarkDataCollection

### CONFIG part
mosWeightsDir = yamlConfig['MOS']['mosWeightsDir']
benchmarkConfig = yamlConfig['benchmark']

userCounts = benchmarkConfig['userCounts']

mosEntryFileName = 'entries.txt'
baseEntryFileName = 'entries_baselines.txt'

userCounts = benchmarkConfig['userCounts']
startMOSEntry = benchmarkConfig['startMOSNumberingFrom']

mosDeploymentFileDir = yamlConfig['MOS']['deploymentFile']

locustFilePath = benchmarkConfig['locustFileLocation']
svcNameToSendLoad = yamlConfig['benchmark']['svcToSendLoad']

loadTimeForEachOne = benchmarkConfig['loadTime']
restPeriod = benchmarkConfig['restPeriod']
dataSaveDir = benchmarkConfig['dataSaveDir']

## Code

with open(mosWeightsDir, "r") as file:
    csv_reader = csv.DictReader(file)
    header = csv_reader.fieldnames
    givenWeights = [{k: float(v) for k, v in row.items()} for row in csv_reader]


def deploy_pods(deploymentFileDir):
    os.system(f'kubectl delete -f {deploymentFileDir}') 
    time.sleep(15)
    os.system(f'kubectl apply -f {deploymentFileDir}') 
    time.sleep(5)

# def checkOutOfCpu():
#     s = run_command("kubectl get pods | awk 'NR > 1 && tolower($3) == \"outofcpu\" { print $3 }' | wc -l")
#     if int(s) > 0:
#         print('OutOfCPU Pods detected. Aborting this test')
#         return 1
#     return 0

def runPreWebLoadTasks(thread_executor, userCount, csvNumber):
    thread_executor.submit(benchmarkDataCollection.runCostMonitor, csvNumber, loadTimeForEachOne, restPeriod)
    time.sleep(restPeriod)

def runPostWebLoadTasks(thread_executor, userCount, csvNumber):
    thread_executor.submit(benchmarkDataCollection.runCPUusage, csvNumber, loadTimeForEachOne, restPeriod)

def benchMOS(start, times):
    csvNumber = start

    file = open(mosEntryFileName,'a')
    data = []

    # remove_stress()
    # create_stress()

    for _ in range(times):
        for userCount in userCounts:
            for weight in givenWeights:
            # for cost in [0, .25, .5, .75]:
                # for i, w in enumerate(jobs):
                    # global LOCUSTFILE
                    # global USERCOUNT
                    # LOCUSTFILE = csv_number
                    # USERCOUNT = user
                    
                    # need to auto load headers
                    cost_weight = weight['cost_weight']
                    net_weight  = weight['net_weight']
                    cpu_weight  = weight['cpu_weight']

                    allScoringFunctions.setWeightForAllScoringFunction(weight)

                    thread_exec = ThreadPoolExecutor()
                    deploy_pods(mosDeploymentFileDir)
                    time.sleep(5)
                    # if checkOutOfCpu():
                    #     continue
                    while pod_info.checkPodsRunning() != True:
                        time.sleep(3)

                    print('Pods are running')

                    newEntry = {'fileNum': csvNumber, 'userCount': userCount}
                    newEntry.update(weight)

                    data.append(newEntry)

                    file.write(str(newEntry))
                    file.write('\n')
                    file.flush()


                    runPreWebLoadTasks(thread_exec, userCount = userCount, csvNumber = csvNumber)
                    
                    thread_exec.submit(utils.runWebLoad, userCount, locustFilePath, loadTimeForEachOne, svcNameToSendLoad, dataSaveDir, csvNumber)
                    time.sleep(loadTimeForEachOne + restPeriod)

                    runPostWebLoadTasks(thread_exec, userCount, csvNumber)

                    time.sleep(30)

                    csvNumber+=1
                    print(f"DONE {csvNumber}")

    # remove_stress()
    file.close()
    print(data)

def benchBaseline(start, times, deploymentFileDir, baselineName):
    csvNumber = start
    file = open(baseEntryFileName,'a')
    data = []

    # remove_stress()
    # create_stress()

    for _ in range(times):
        for userCount in userCounts:
            thread_exec = ThreadPoolExecutor()
            deploy_pods(deploymentFileDir)
            time.sleep(5)

            while pod_info.checkPodsRunning() != True:
                time.sleep(3)

            data.append({'fileNum': csvNumber, 'baseline':baselineName, 'user': userCount})

            file.write(str(data[-1]))
            file.write('\n')
            file.flush()

            runPreWebLoadTasks(thread_exec, userCount = userCount, csvNumber = csvNumber)
            
            thread_exec.submit(utils.runWebLoad, userCount, locustFilePath, loadTimeForEachOne, svcNameToSendLoad, dataSaveDir, csvNumber)
            time.sleep(loadTimeForEachOne + restPeriod)

            runPostWebLoadTasks(thread_exec, userCount, csvNumber)

            time.sleep(30)

            csvNumber += 1
            print(f"DONE {csvNumber}")

    # remove_stress()
    file.close()
    print(data)

def benchNetMarks(start, times, deploymentFileDir, baselineName):
    csvNumber = start

    file = open(baseEntryFileName,'a')
    data = []

    for _ in range(times):
        for userCount in userCounts:
            weight = {}

            for scoringFunction in allScoringFunctions.scoringFunctions:
                if scoringFunction.weightHeader == 'net_weight':
                    weight.update({'net_weight': 1.0})
                else:
                    weight.update({scoringFunction.weightHeader: 0.0})

            allScoringFunctions.setWeightForAllScoringFunction(weight)

            thread_exec = ThreadPoolExecutor()
            deploy_pods(deploymentFileDir)
            time.sleep(5)

            while pod_info.checkPodsRunning() != True:
                time.sleep(3)

            print('Pods are running')

            data.append({'fileNum': csvNumber, 'baseline':baselineName, 'user': userCount})

            file.write(str(data[-1]))
            file.write('\n')
            file.flush()


            runPreWebLoadTasks(thread_exec, userCount = userCount, csvNumber = csvNumber)
            
            thread_exec.submit(utils.runWebLoad, userCount, locustFilePath, loadTimeForEachOne, svcNameToSendLoad, dataSaveDir, csvNumber)
            time.sleep(loadTimeForEachOne + restPeriod)

            runPostWebLoadTasks(thread_exec, userCount, csvNumber)

            time.sleep(30)

            csvNumber+=1
            print(f"DONE {csvNumber}")

    # remove_stress()
    file.close()
    print(data)

### Custom Benchmark Function