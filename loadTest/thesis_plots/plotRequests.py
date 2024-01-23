import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/loadTest/')

class EntryLoader :
    def __init__(self):
        file = open('entries.txt', 'r')
        lines = file.readlines()
        self.datas = defaultdict(list)
        for line in lines:
            line = eval(line)
            cost = line['cost_weight']
            net = line['net_weight']
            cpu = line['cpu_weight']
            # make net and cpu weights relative to each other
            if cost != 1:
                net = net / (1-cost)
                cpu = cpu / (1-cost)
            weights = (net,cpu,cost, line['userCount'])
            self.datas[weights].append(line['fileNum'])

    # filters fileNumbers from datas, gives a single value even if there are multiples
    def filter(self, net_weight:list = None, cpu_weight:list = None, cost_weight:list = None, userCount:list = None):
        filteredDatas = defaultdict(list)
        for key, values in self.datas.items():
            if ((net_weight is None or key[0] in net_weight) and
                (cpu_weight is None or key[1] in cpu_weight) and
                (cost_weight is None or key[2] in cost_weight) and
                (userCount is None or key[3] in userCount)):
                    filteredDatas[key] = values
        return filteredDatas
    
    def getTotalRequests(self, datas: defaultdict(list)):
        requestDict = defaultdict(int)
        for key,values in datas.items():
            request = 0
            for value in values:
                df = pd.read_csv('data/hpdc/'+str(value)+'_stats_history.csv')
                df = df[df['Name'] == 'Aggregated']
                mn = df['Timestamp'].min()
                df.loc[:, ('Timestamp')] = df.loc[:, ('Timestamp')] - mn
                df = df[df['Timestamp'] > 20]
                request += df['Total Request Count'].max()
            request /= len(values) # take avg of all available data, if we run multiple benchmarks
            requestDict[key] = request
        return requestDict

class BaseLineLoader :
    def __init__(self):
        file = open('entries_baselines.txt', 'r')
        lines = file.readlines()
        self.datas = defaultdict(list)
        for line in lines:
            line = eval(line)
            self.datas[line['baseline'], line['user']].append(line['fileNum'])
    
    def filter(self, baseline:list = None, user:list = None):
        filterData = defaultdict(list)
        for key, values in self.datas.items():
            if ((baseline is None or key[0] in baseline) and
               (user is None or key[1] in user)):
                filterData[key] = values
        return filterData
    
    def getTotalRequests(self, datas: defaultdict(list)):
        requestDict = defaultdict(int)
        for key, values in datas.items():
            request = 0
            for value in values:
                df = pd.read_csv('data/baselines/'+str(value)+'_stats_history.csv')
                df = df[df['Name'] == 'Aggregated']
                mn = df['Timestamp'].min()
                df.loc[:, ('Timestamp')] = df.loc[:, ('Timestamp')] - mn
                df = df[df['Timestamp'] > 20]
                request += df['Total Request Count'].max()
            request /= len(values) # take avg of all available data, if we run multiple benchmarks
            requestDict[key] = request
        return requestDict

entries = EntryLoader()
filteredDatas = entries.filter(userCount=[1000], cost_weight=[0,.25,.5])
requests = entries.getTotalRequests(filteredDatas)
print(requests)

cost_weights = sorted(set(key[2] for key in requests.keys()))
net_weights = sorted(set(key[0] for key in requests.keys()))
print(net_weights)

palette = sns.color_palette("tab10")
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Adjust the bottom space
legend_entries = []
bar_width = .2  # Width of individual bars
group_width = bar_width * len(cost_weights)  # The total width of a group
gap_width = 0.3 # Width of the gap between groups
index = np.arange(len(net_weights)) * (group_width + gap_width) 

baselines = 2
baselineLoader = BaseLineLoader()
# ax.bar(bar_width+gap_width, 60000, bar_width, label='netMarks', color=palette[-2])

filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks'],user=[1000])
print(filteredBaselines)
baselinesRequest = baselineLoader.getTotalRequests(filteredBaselines)
print('baselineReq\n', baselinesRequest)
ax.bar(0, baselinesRequest[('default',1000)], bar_width, label='default', color=palette[-1])
ax.bar(bar_width+gap_width, baselinesRequest[('netmarks',1000)], bar_width, label='netMarks', color=palette[-2])

for i, cw in enumerate(cost_weights):
    sameNetRequests = []
    for j, nw in enumerate(net_weights):
        for key, value in requests.items():
            if key[0] == nw and key[2] == cw:
                sameNetRequests.append(value)
    bar = ax.bar(baselines * (bar_width+gap_width) + index + i * bar_width, sameNetRequests, bar_width, label=f'Cost Weight {cw}', color=palette[i])
    legend_entries.append(bar)

ax.set_xlabel('Net Weight(Relative)')
ax.set_ylabel('Total Requests')
ax.set_title('Total Requests by Net Weight and Cost Weight')
xticks = [i * (bar_width+gap_width) for i in range(baselines)]
xticks.extend(baselines * (bar_width+gap_width) + index + group_width / 2 - bar_width / 2)
print(xticks)
ax.set_xticks(xticks)
ax.set_xticklabels(['default', 'netMarks'] + [f'{weight}' for weight in net_weights])
ax.tick_params(axis='x', labelrotation=45)
ax.legend(handles=legend_entries, loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=len(cost_weights), fontsize='x-small')

plt.tight_layout()
plt.savefig('thesis_plots/images/Total_Requests_1000user.png')