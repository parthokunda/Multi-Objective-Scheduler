import sqlite3
import config

conn = sqlite3.connect(config.SCHEDULER_DATABASE_DIR)
cursor = conn.cursor()

cursor.execute('''SELECT source_app,destination_app, rate from netRate;''')
netRates = cursor.fetchall()

netRatesDict = {}
for src_app, dest_app, rate in netRates:
    key = (src_app, dest_app)
    netRatesDict[key] = rate

cursor.execute('''SELECT source_app, rate from cpuRate;''')
cpuRates = cursor.fetchall()

cpuRatesDict = {}
for app_name, cpu in cpuRates:
    cpuRatesDict[app_name] = cpu

conn.close()

def getCpuForApp(appName: str) -> float:
    if appName not in cpuRatesDict:
        raise Exception(f"CPU data for {appName} not found in the database")
    return cpuRatesDict[appName]

def getNetForApp(srcAppName: str, destAppName: str) -> float:
    key = (srcAppName, destAppName)
    if key not in netRatesDict:
        raise Exception(f"Network data for {srcAppName}, {destAppName} not found in the database")
    return netRatesDict[key]