from config.config import yamlConfig
from benchmark.bench import benchMOS, benchBaseline
import os, importlib.util
from concurrent.futures import ThreadPoolExecutor
import mosscheduler

thread_exec = ThreadPoolExecutor()

isBenchmarkEnabled = yamlConfig['benchmark']['enabled']

if not isBenchmarkEnabled:
    print("Benchmark is not enabled")
    exit()

startingNumForMosData = yamlConfig['benchmark']['startMOSNumberingFrom']
repetitions = yamlConfig['benchmark']['repetitions']
dataSaveDir = yamlConfig['benchmark']['dataSaveDir']

if not os.path.exists(dataSaveDir):
    os.makedirs(dataSaveDir)

thread_exec.submit(mosscheduler.run_scheduler)
# benchMOS(startingNumForMosData, repetitions)

baselineConfigList = yamlConfig['benchmark']['baselines']

for baselineConfig in baselineConfigList:
    name = baselineConfig['name']
    startCsvNumber = baselineConfig['startCsvNumber']
    deploymentFile = baselineConfig['deploymentFile']
    useCustomBenchmarkFunction = baselineConfig['useCustomBenchmarkFunction']

    if useCustomBenchmarkFunction:
        benchmarkFunctionName = baselineConfig['customBenchmarkFunctionName']
        module_name = 'benchmark.bench'
        module = importlib.import_module(module_name)
        function_to_call = getattr(module, benchmarkFunctionName)
        function_to_call(startCsvNumber, repetitions, deploymentFile, name)

    else:
        benchBaseline(startCsvNumber, repetitions, deploymentFile, name)
    
    # print("You can close now. The benchmark is finished.")