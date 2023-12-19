import pandas as pd
import matplotlib.pyplot as plt

dfs = []
files = ['1-costMonitor.csv',
         '2-costMonitor.csv', 
         '3-costMonitor.csv', 
         '4-costMonitor.csv',
         '5-costMonitor.csv']
labels = ['default','.25', '.5', '.75', '1']

for file in files:
    dfs.append(pd.read_csv('data/'+file))

cost = []
for df in dfs:
    cost.append(df['avgCost'].iloc[-1])


plt.bar(labels, cost)
plt.title("Cost on avg - CPU Usage Incorporated")
plt.savefig("images/Cost on avg - CPU Usage Incorporated.png")