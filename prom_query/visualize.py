import os
import pandas as pd
import matplotlib.pyplot as plt

directory_path = '/home/partho/Desktop/Thesis Repo/prom_query/binpack'

for filename in os.listdir():
    if filename.endswith(".csv"):
        file_path = os.path.join(directory_path, filename)

        df = pd.read_csv(file_path)

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        plt.plot(df['timestamp'], df['value'], marker='o', linestyle='-', label=filename)
        plt.figure()
        plt.legend()
        plt.title('Timestamp vs. '+filename)
        plt.xlabel('Timestamp')
        plt.ylabel('Value')
        plt.grid(True)
        break


plt.show()
