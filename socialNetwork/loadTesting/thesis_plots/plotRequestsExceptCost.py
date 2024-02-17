import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/loadTest/')
USERS = [50,500,1000,2000]
FILENAME = 'entries.txt'
BASEFILENAME = 'entries_baselines.txt'

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
filteredDatas = entries.filter(userCount=USERS, cost_weight=[0])
print(filteredDatas)
requests = entries.getTotalRequests(filteredDatas)
print(requests)

net_weights = sorted(set(key[0] for key in requests.keys()))


palette = sns.color_palette("tab10")
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Adjust the bottom space
legend_entries = []
bar_width = .2  # Width of individual bars
group_width = bar_width * len(net_weights)  # The total width of a group
gap_width = 0.3 # Width of the gap between groups
index = np.arange(len(USERS)) * (group_width + gap_width) 

baselines = 0
baselineLoader = BaseLineLoader()

for j, nw in enumerate(net_weights):
    for i, user in enumerate(USERS):
        for key, value in requests.items():
            if key[0] == nw and key[3] == user:
                bar = ax.bar(index[i] + j * bar_width, value, bar_width, label=f'(α,β)=({nw},{1-nw})', color=palette[j])
                if i == 0:
                    legend_entries.append(bar)

def RtToK(x,pos):
    return f'{int(x//1000)}K'
ax.yaxis.set_major_formatter(FuncFormatter(RtToK))
ax.set_ylabel('$R_t$')
xticks = []
xticks.extend(index + group_width / 2 - bar_width / 2)
ax.set_xticks(xticks)
ax.set_xticklabels( [f'N={user}' for user in USERS])
ax.legend(handles=legend_entries, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=len(net_weights)/2, fontsize='medium')

plt.tight_layout()
plt.savefig(f'thesis_plots/images/v2Total_Requests_ExceptCost.png', dpi=300, bbox_inches='tight')