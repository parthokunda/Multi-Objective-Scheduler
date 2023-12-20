import pandas as pd
import matplotlib.pyplot as plt

dfs = []
files = ['8-costMonitor.csv',
         '6-costMonitor.csv', 
         '7-costMonitor.csv']
labels = ['.2', '.33', '.5']

for file in files:
    dfs.append(pd.read_csv('data/'+file))

cost = []
for df in dfs:
    cost.append(df['avgCost'].iloc[-1])


plt.bar(labels, cost)
plt.title("Cost on avg - Cost Incorporated")
plt.savefig("images/Cost on avg - Cost Incorporated.png")