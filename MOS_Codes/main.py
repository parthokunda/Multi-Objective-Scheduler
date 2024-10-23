from config.config import yamlConfig
from benchmark.bench import benchMOS
import os
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
benchMOS(startingNumForMosData, repetitions, dataSaveDir)