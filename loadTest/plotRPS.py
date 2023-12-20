import pandas as pd
import matplotlib.pyplot as plt

dfs = []
files = ['8-v2_load_2500_8m_stats_history.csv',
         '6-v2_load_2500_8m_stats_history.csv', 
         '7-v2_load_2500_8m_stats_history.csv']
labels = ['.2', '.33', '.5']

for file in files:
    dfs.append(pd.read_csv('data/'+file))

for i, df in enumerate(dfs):
    dfs[i] = df[df['Name'] == 'Aggregated']
    mn = dfs[i]['Timestamp'].min()
    dfs[i].loc[:, ('Timestamp')] = dfs[i].loc[:, ('Timestamp')] - mn

fig, axs = plt.subplots(2,2,figsize=(12,8))

def plot(axs, dfs, labels, axis:tuple, x = 'Timestamp', y='Requests/s'):
    for i in range(len(dfs)):
        axs[axis[0], axis[1]].plot(dfs[i][x], dfs[i][y], label = labels[i])
        axs[axis[0], axis[1]].grid(True)
        axs[axis[0], axis[1]].set_xlabel(x)
        axs[axis[0], axis[1]].set_ylabel(y)
        axs[axis[0], axis[1]].legend()

def plotBar(axs, categories, values, axis:tuple, y):
    axs[axis[0], axis[1]].bar(categories, values)
    axs[axis[0], axis[1]].set_ylabel(y)

failure = [df['Total Failure Count'].max() for df in dfs]
request = [df['Total Request Count'].max() for df in dfs]
plot(axs, dfs, labels, axis=(0,0), y = 'Requests/s')
plotBar(axs, labels, failure, axis=(0,1), y='Failure Count')
plot(axs, dfs, labels, axis=(1,0), y = 'Total Median Response Time')
plotBar(axs, labels, request, axis=(1,1), y='Request Count')


fig.suptitle("Net Stats - 2500user 100spawn 8minute - .2 means 20% cost weight, rest divided equally between CPU and Network")
plt.savefig('images/Net Stats - Incorporating Cost.png')