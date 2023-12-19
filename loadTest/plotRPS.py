import pandas as pd
import matplotlib.pyplot as plt

dfs = []
files = ['1-v1_load_2500_8m_stats_history.csv','2-v1_load_2500_8m_stats_history.csv', '3-v1_load_2500_8m_stats_history.csv', '4-v1_load_2500_8m_stats_history.csv',
         '5-v1_load_2500_8m_stats_history.csv']
labels = ['default','.25', '.5', '.75', '1']

for file in files:
    dfs.append(pd.read_csv(file))

for i, df in enumerate(dfs):
    dfs[i] = df[df['Name'] == 'Aggregated']
    mn = dfs[i]['Timestamp'].min()
    dfs[i].loc[:, ('Timestamp')] = dfs[i].loc[:, ('Timestamp')] - mn



# default = pd.read_csv('1-default_load_2500_8m_stats_history.csv')
# two = pd.read_csv('2-v1_load_2500_8m_stats_history.csv')
# three = pd.read_csv('3-v1_load_2500_8m_stats_history.csv')
# four = pd.read_csv('4-v1_load_2500_8m_stats_history.csv')

# default = default[default['Name'] == 'Aggregated']
# two = two[two['Name'] == 'Aggregated']
# three = three[three['Name'] == 'Aggregated']
# four = four[four['Name'] == 'Aggregated']

# nM_start = nM['Timestamp'].min()
# v1_start = v1['Timestamp'].min()

# nM['Timestamp'] = nM['Timestamp'] - nM_start
# v1['Timestamp'] = v1['Timestamp'] - v1_start

# default['Timestamp'] = default['Timestamp']  - default['Timestamp'].min()
# two['Timestamp'] = two['Timestamp']  - two['Timestamp'].min()
# three['Timestamp'] = three['Timestamp']  - three['Timestamp'].min()
# four['Timestamp'] = four['Timestamp']  - four['Timestamp'].min()

# default = default[default['Timestamp'] >= 100]
# two = two[two['Timestamp'] >= 100]
# three = three[three['Timestamp'] >= 100]
# four = four[four['Timestamp'] >= 100]

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
# plot(axs, dfs, labels, axis=(0,1), y = '99%')
plotBar(axs, labels, failure, axis=(0,1), y='Failure Count')
plot(axs, dfs, labels, axis=(1,0), y = 'Total Median Response Time')
# plot(axs, dfs, labels, axis=(1,1), y = 'Total Request Count')
plotBar(axs, labels, request, axis=(1,1), y='Request Count')


fig.suptitle("CPU status - 2500user 100spawn 5minute - .25 means 25% network weight")
plt.savefig('Incorporating CPU Stats.png')