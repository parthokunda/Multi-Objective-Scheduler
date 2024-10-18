"""
This file when imported should do the following
- Create a database file if it does not exist
- Query Prometheus and update the database
"""

import utils
import sqlite3
from mos_logger import mos_logger as mos_log
from config import yamlConfig

def initDb(cursor, conn):
        mos_log.info("Creating Database Tables")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS netRate (
                source_app TEXT NOT NULL,
                destination_app TEXT NOT NULL,
                rate REAL NOT NULL,
                timeframes INT NOT NULL,
                UNIQUE(source_app, destination_app) ON CONFLICT REPLACE,
                CHECK (source_app <> destination_app)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpuRate (
                source_app TEXT NOT NULL,
                rate REAL NOT NULL,
                timeframes INT NOT NULL,
                UNIQUE(source_app) ON CONFLICT REPLACE
            )
        ''')
        sample_data = []

        for appsrc in appNames:
            for appdest in appNames:
                if appsrc == appdest:
                    continue
                sample_data.append((appsrc, appdest, 0.0, 0))

        cursor.executemany('INSERT INTO netRate (source_app, destination_app, rate, timeframes) VALUES (?, ?,  ?, ?)', sample_data)

        cpu_init_data = []
        for app in appNames:
            cpu_init_data.append((app, 0.0, 0))

        cursor.executemany('INSERT INTO cpuRate (source_app, rate, timeframes) VALUES (?, ?, ?)', cpu_init_data)
        conn.commit()


### this block should run when the file is imported
print("Setting up the database")
appNames = utils.getAllAppNames()

shouldInitDb = yamlConfig['database']['shouldInitDb']
dbPath = yamlConfig['database']['path']

conn = sqlite3.connect(dbPath)
cursor = conn.cursor()

if shouldInitDb:
    initDb(cursor=cursor, conn=conn)


conn.close()