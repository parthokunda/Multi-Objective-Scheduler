import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

dfs = []
slas = []
files = [48,49,50,51,52]
labels = ['0', '0.09375', '0.1875', '0.28125', '0.375']

for file in files:
    print(file)
    dfs.append(pd.read_csv('data/'+str(file)+'_stats_history.csv'))
    slas.append(pd.read_csv('data/'+str(file)+'-SLA.csv'))

for i, df in enumerate(dfs):
    dfs[i] = df[df['Name'] == 'Aggregated']
    mn = dfs[i]['Timestamp'].min()
    dfs[i].loc[:, ('Timestamp')] = dfs[i].loc[:, ('Timestamp')] - mn
    dfs[i] = dfs[i][dfs[i]['Timestamp'] > 15]

fig, axs = plt.subplots(2,2,figsize=(12,8))

def plot(axs, dfs, labels, axis:tuple, x = 'Timestamp', y='Requests/s'):
    for i in range(len(dfs)):
        axs[axis[0], axis[1]].plot(dfs[i][x], dfs[i][y], label = labels[i])
        axs[axis[0], axis[1]].grid(True)
        axs[axis[0], axis[1]].set_xlabel(x)
        axs[axis[0], axis[1]].set_ylabel(y)
        axs[axis[0], axis[1]].legend()

def plotSLA(axs, slas, labels, axis:tuple, x = 'Timestamp', y='Requests/s', slaLimits=[500, 1000, 2000]):
    slaViolatePercent = [[0] * len(slas) for _ in range(len(slaLimits))]
    
    for slaIndex, sla in enumerate(slas):
        for limitIndex, slaLimit in enumerate(slaLimits):
            slaViolatePercent[limitIndex][slaIndex] = (sla['response_time'] > slaLimit).sum() / len(sla) * 100
    indices = np.arange(len(slas))
    # print(indices)
    # print(slaViolatePercent)
    for limitIndex in range(len(slaLimits)):
        axs[axis[0], axis[1]].bar(indices + limitIndex * .25, slaViolatePercent[limitIndex], width=.25, label=slaLimits[limitIndex])
    axs[axis[0], axis[1]].set_xticks(indices + ((len(slaLimits) - 1) / 2.0) * 0.25, labels)
    axs[axis[0], axis[1]].legend()
    
def plotSLA2(axs, slas, labels, axis:tuple, x = 'Timestamp', y='Requests/s'):
    slaLimits = np.linspace(500, 3000, 10)
    for slaIndex, sla in enumerate(slas):
        slaViolationPerLimit = []
        for limitIndex, limit in enumerate(slaLimits):
            slaViolationPerLimit.append((sla['response_time'] > limit).sum() / len(sla) * 100)
        axs[axis[0], axis[1]].plot(slaLimits, slaViolationPerLimit, label = labels[slaIndex])
    axs[axis[0], axis[1]].legend()

def plotBar(axs, categories, values, axis:tuple, y):
    axs[axis[0], axis[1]].bar(categories, values)
    axs[axis[0], axis[1]].set_ylabel(y)

failure = [df['Total Failure Count'].max() for df in dfs]
request = [df['Total Request Count'].max() for df in dfs]
slaLimit = 2000
plotSLA2(axs, slas, labels, axis=(0,0), y=f'SLA ({slaLimit}ms) Violated %')
plotBar(axs, labels, failure, axis=(0,1), y='Failure Count')
plot(axs, dfs, labels, axis=(1,0), y = 'Total Median Response Time')
plotBar(axs, labels, request, axis=(1,1), y='Request Count')


fig.suptitle("Net Stats - 500user 100spawn 3minute - Cost set at .25 weight, Labels are net weight")
plt.savefig('images/x_Net Stats')