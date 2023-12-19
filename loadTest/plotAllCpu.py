import pandas as pd
import matplotlib.pyplot as plt

dfs = []
dfsByNodes : list[dict] = {}
nodes = ['k8s-vm1','k8s-vm2','k8s-vm3','k8s-vm5']
files = ['1-cpuUsage.csv','2-cpuUsage.csv', '3-cpuUsage.csv', '4-cpuUsage.csv',
         '5-cpuUsage.csv']
labels = ['default','.25', '.5', '.75', '1']

for file in files:
    dfs.append(pd.read_csv("./data/"+file))

for i, df in enumerate(dfs):
    mx = dfs[i]['timestamp'].max()
    dfs[i].loc[:, ('timestamp')] = dfs[i][dfs[i]['timestamp'] > mx - 600]
    mn = dfs[i]['timestamp'].min()
    dfs[i].loc[:, ('timestamp')] = dfs[i].loc[:, ('timestamp')] - mn
    # nodeCPU = {}
    # for node in nodes:
    #     nodeCPU[node] = dfs[i][dfs[i]['node_name'] == 'k8s-vm1']
    # dfsByNodes.append(nodeCPU)

# nMCPU = pd.read_csv('netMarks_load_2500_5m_cpuUsage.csv')
# v1CPU = pd.read_csv('v1_load_2500_5m_cpuUsage.csv')

# nM_start = nMCPU['timestamp'].min()
# v1_start = v1CPU['timestamp'].min()

# nMCPU['timestamp'] = nMCPU['timestamp'] - nM_start
# v1CPU['timestamp'] = v1CPU['timestamp'] - v1_start

# nMvm1 = nMCPU[nMCPU['node_name'] == 'k8s-vm1']
# nMvm2 = nMCPU[nMCPU['node_name'] == 'k8s-vm2']
# nMvm3 = nMCPU[nMCPU['node_name'] == 'k8s-vm3']

# v1vm1 = v1CPU[nMCPU['node_name'] == 'k8s-vm1']
# v1vm2 = v1CPU[nMCPU['node_name'] == 'k8s-vm2']
# v1vm3 = v1CPU[nMCPU['node_name'] == 'k8s-vm3']


# datalowdefault = datalowdefault[datalowdefault['Requests/s'] > 0]
# datahighdefault = datahighdefault[datahighdefault['Requests/s'] > 0]
# # datalowdefault['Readable_Time'] = pd.to_datetime(datalowdefault['Timestamp'], unit='s')
# # print(datalowdefault['Readable_Time'])

fig, axs = plt.subplots(5,1,figsize=(24,16))

def plotNodeUsage(df, axs, nodesList, axis, label ,x = 'timestamp', y='value'):
    for node in nodesList:
        axs[axis].plot( df[df['node_name'] == node][x], df[df['node_name'] == node][y], label = node)
        axs[axis].grid(True)
        axs[axis].set_ylabel(label)
        axs[axis].legend()

for i in range(len(dfs)):
    plotNodeUsage(dfs[i], axs, nodes, i, labels[i])


fig.suptitle("CPU Stats - 2500user 100spawn 5minute - .25 means 25% network usage")
plt.savefig('images/CPU stats - Incorporated CPU usage.png')