import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

dfs = []
slas = []
files = [87, 88, 89, 90, 91, 92, 93, 94, 95 ]
labels = [ '0', '.125', '.25', '.375', '.5', '.625', '.75', '.875', '1.0']
costs = []

for file in files:
    print(file)
    dfs.append(pd.read_csv('data/'+str(file)+'_stats_history.csv'))
    slas.append(pd.read_csv('data/'+str(file)+'-SLA.csv'))
    costs.append(pd.read_csv('data/'+str(file)+'-costMonitor.csv'))

for i, df in enumerate(dfs):
    dfs[i] = df[df['Name'] == 'Aggregated']
    mn = dfs[i]['Timestamp'].min()
    dfs[i].loc[:, ('Timestamp')] = dfs[i].loc[:, ('Timestamp')] - mn
    dfs[i] = dfs[i][dfs[i]['Timestamp'] > 15]


fig, axs = plt.subplots(2,2,figsize=(16,12))

def plotCost(axs, labels, axis:tuple, x = 'Net Weight', y='Avg Cost'):
    for i, costDF in enumerate(costs):
        costs[i] = costs[i]['avgCost'].iloc[-1]
    axs[axis[0], axis[1]].bar(labels, costs)
    axs[axis[0], axis[1]].set_ylabel("Average Cost")
    axs[axis[0], axis[1]].set_title("Avg Cost Per Minute")


def plot(axs, dfs, labels, axis:tuple, x = 'Timestamp', y='Requests/s'):
    for i in range(len(dfs)):
        axs[axis[0], axis[1]].plot(dfs[i][x], dfs[i][y], label = labels[i])
        axs[axis[0], axis[1]].grid(True)
    axs[axis[0], axis[1]].set_xlabel("Seconds")
    axs[axis[0], axis[1]].set_ylabel(y)
    axs[axis[0], axis[1]].set_title("Response Time over Time")
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
    axs[axis[0], axis[1]].set_xlabel("ms")
    axs[axis[0], axis[1]].set_ylabel("Violation Percentage")
    axs[axis[0], axis[1]].set_title("SLA Violation Graph")
    axs[axis[0], axis[1]].legend()

    
def plotSLA2(axs, slas, labels, axis:tuple, x = 'Timestamp', y='Requests/s'):
    slaLimits = np.linspace(50, 1500, 10)
    for slaIndex, sla in enumerate(slas):
        slaViolationPerLimit = []
        for limitIndex, limit in enumerate(slaLimits):
            slaViolationPerLimit.append((sla['response_time'] > limit).sum() / len(sla) * 100)
        axs[axis[0], axis[1]].plot(slaLimits, slaViolationPerLimit, label = labels[slaIndex])
    axs[axis[0], axis[1]].set_xlabel("ms")
    axs[axis[0], axis[1]].set_ylabel("Violation Percentage")
    axs[axis[0], axis[1]].set_title("SLA Violation Graph")
    axs[axis[0], axis[1]].legend()

def plotBar(axs, categories, values, axis:tuple, y):
    axs[axis[0], axis[1]].bar(categories, values)
    axs[axis[0], axis[1]].set_ylabel(y)
    axs[axis[0], axis[1]].set_title("Total Requests For Weights")


failure = [df['Total Failure Count'].max() for df in dfs]
request = [df['Total Request Count'].max() for df in dfs]
slaLimit = 2000
plotSLA2(axs, slas, labels, axis=(0,0), y=f'SLA ({slaLimit}ms) Violated %')
# plotBar(axs, labels, failure, axis=(0,1), y='Failure Count')
plotCost(axs, labels, axis=(0,1))
plot(axs, dfs, labels, axis=(1,0), y = 'Total Median Response Time')
plotBar(axs, labels, request, axis=(1,1), y='Request Count')


fig.suptitle("Cost = 0.375, Net Weight = .25(relative) CPU Weight .75(relative)\nUser Count = 2000")
plt.savefig('images/x_Stats')