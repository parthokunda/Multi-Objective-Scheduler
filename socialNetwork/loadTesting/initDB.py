import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

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

app_list = set([
"compose-post-service",
"home-timeline-redis",
"home-timeline-service",
"jaeger",
"media-frontend",
"media-memcached",
"media-mongodb",
"media-service",
"nginx-thrift",
"post-storage-memcached",
"post-storage-mongodb",
"post-storage-service",
"social-graph-mongodb",
"social-graph-redis",
"social-graph-service",
"text-service",
"unique-id-service",
"url-shorten-memcached",
"url-shorten-mongodb",
"url-shorten-service",
"user-memcached",
"user-mention-service",
"user-mongodb",
"user-service",
"user-timeline-mongodb",
"user-timeline-redis",
"user-timeline-service",
])


sample_data = []

for appsrc in app_list:
    for appdest in app_list:
        if appsrc == appdest:
            continue
        sample_data.append((appsrc, appdest, 0.0, 0))

cursor.executemany('INSERT INTO netRate (source_app, destination_app, rate, timeframes) VALUES (?, ?,  ?, ?)', sample_data)

cpu_init_data = []
for app in app_list:
    cpu_init_data.append((app, 0.0, 0))

cursor.executemany('INSERT INTO cpuRate (source_app, rate, timeframes) VALUES (?, ?, ?)', cpu_init_data)

conn.commit()

conn.close()
