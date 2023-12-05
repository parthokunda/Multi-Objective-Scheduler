import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS app_matrix (
        source_app TEXT NOT NULL,
        destination_app TEXT NOT NULL,
        rate REAL NOT NULL,
        timeframes INT NOT NULL,
        UNIQUE(source_app, destination_app) ON CONFLICT REPLACE
    )
''')

app_list = set([
    "adservice", 
    "cartservice", 
    "checkoutservice", 
    "currencyservice", 
    "emailservice", 
    "frontend", 
    "loadgenerator", 
    "paymentservice", 
    "productcatalogservice", 
    "recommendationservice", 
    "redis-cart", 
    "shippingservice"
])

sample_data = []

for appsrc in app_list:
    for appdest in app_list:
        if appsrc == appdest:
            continue
        sample_data.append((appsrc, appdest, 0.0, 0))

cursor.executemany('INSERT INTO app_matrix (source_app, destination_app, rate, timeframes) VALUES (?, ?, ?, ?)', sample_data)

conn.commit()

conn.close()