import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

dfs = []
slas = []
files = [200, 201, 202, 203, 204, 205]
labels = [50, 100, 500, 1000, 1500, 2000]
for i, _ in enumerate(labels):
    labels[i] = str(labels[i])

costs = []

for file in files:
    print(file)
    dfs.append(pd.read_csv(str(file)+'_stats_history.csv'))
    slas.append(pd.read_csv(str(file)+'-SLA.csv'))
    costs.append(pd.read_csv(str(file)+'-costMonitor.csv'))

for i, df in enumerate(dfs):
    dfs[i] = df[df['Name'] == 'Aggregated']
    mn = dfs[i]['Timestamp'].min()
    dfs[i].loc[:, ('Timestamp')] = dfs[i].loc[:, ('Timestamp')] - mn
    dfs[i] = dfs[i][dfs[i]['Timestamp'] > 15]

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

    
def plotSLA2(slas, labels, x = 'Timestamp', y='Requests/s'):
    slaLimits = np.linspace(0, 5000, 50)
    for slaIndex, sla in enumerate(slas):
        slaViolationPerLimit = []
        for limitIndex, limit in enumerate(slaLimits):
            slaViolationPerLimit.append((sla['response_time'] > limit).sum() / len(sla) * 100)
        ax1.plot(slaLimits, slaViolationPerLimit, label = labels[slaIndex])
    ax1.set_xlabel("ms", fontsize="xx-large")
    ax1.set_ylabel("Violation Percentage", fontsize='xx-large')
    ax1.set_title("SLA Violation Graph", fontsize='xx-large')
    ax1.tick_params(axis='x', labelrotation=45, labelsize='xx-large')
    ax1.tick_params(axis='y', labelsize='xx-large')
    ax1.legend(fontsize='xx-large')

# def plotBar(categories, values, y):
#     ax2.bar(categories, values)
#     print(categories, values)
#     ax2.set_ylabel(y, fontsize='xx-large')
#     ax2.set_title("Total Requests For Weights", fontsize='xx-large')
#     ax2.tick_params(axis='x', labelrotation=45, labelsize='xx-large')
#     ax2.tick_params(axis='y', labelsize='xx-large')


failure = [df['Total Failure Count'].max() for df in dfs]
request = [df['Total Request Count'].max() for df in dfs]
slaLimit = 2000
fig, (ax1, ax2) = plt.subplots(1,2,figsize=(24,12))
print(labels)
print(request)
ax2.bar(labels, request)
# plotBar(axs, labels, failure, axis=(0,1), y='Failure Count')
# plotCost(axs, labels, axis=(0,1))
# plot(axs, dfs, labels, axis=(1,0), y = 'Total Median Response Time')
# plotBar( labels, request, y='Request Count')
plotSLA2(slas, labels, y=f'SLA ({slaLimit}ms) Violated %')


# fig.tight_layout(pad=4)
plt.savefig('images/x_Net_Stats')