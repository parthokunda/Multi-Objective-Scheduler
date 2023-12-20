import pandas as pd
import matplotlib.pyplot as plt

dfs = []
dfsByNodes : list[dict] = {}
nodes = ['k8s-vm1','k8s-vm2','k8s-vm3','k8s-vm5']
files = ['8-cpuUsage.csv',
         '6-cpuUsage.csv', 
         '7-cpuUsage.csv']
labels = ['.2', '.33', '.5']

for file in files:
    dfs.append(pd.read_csv("./data/"+file))

for i, df in enumerate(dfs):
    mx = dfs[i]['timestamp'].max()
    dfs[i].loc[:, ('timestamp')] = dfs[i][dfs[i]['timestamp'] > mx - 600]
    mn = dfs[i]['timestamp'].min()
    dfs[i].loc[:, ('timestamp')] = dfs[i].loc[:, ('timestamp')] - mn


fig, axs = plt.subplots(len(files),1,figsize=(24,16))

def plotNodeUsage(df, axs, nodesList, axis, label ,x = 'timestamp', y='value'):
    for node in nodesList:
        axs[axis].plot( df[df['node_name'] == node][x], df[df['node_name'] == node][y], label = node)
        axs[axis].grid(True)
        axs[axis].set_ylabel(label)
        axs[axis].legend()

for i in range(len(dfs)):
    plotNodeUsage(dfs[i], axs, nodes, i, labels[i])


fig.suptitle("CPU Stats - 2500user 100spawn 8minute - .2 means 20% cost weight, rest divided equally between CPU and Network")
plt.savefig('images/CPU stats - Incorporated Cost.png')