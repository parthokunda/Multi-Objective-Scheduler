import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/loadTest/')
FILENAME = 'entries.txt'
BASEFILENAME = 'entries_baselines.txt'

class EntryLoader :
    def __init__(self):
        file = open(FILENAME, 'r')
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

    def filter(self, net_weight:list = None, cpu_weight:list = None, cost_weight:list = None, userCount:list = None):
        filteredDatas = defaultdict(list)
        for key, values in self.datas.items():
            if ((net_weight is None or key[0] in net_weight) and
                (cpu_weight is None or key[1] in cpu_weight) and
                (cost_weight is None or key[2] in cost_weight) and
                (userCount is None or key[3] in userCount)):
                    filteredDatas[key] = values
        return filteredDatas
    
    def getCost(self, datas):
        costDict = defaultdict(list)
        for key,values in datas.items():
            cost = 0
            for value in values:
                df = pd.read_csv('data/hpdc/'+str(value)+'-costMonitor.csv')
                cost += df['avgCost'].iloc[-1]
            cost /= len(values)
            costDict[(key[0], key[1], key[2])] = cost
        return costDict

class BaseLineLoader :
    def __init__(self):
        file = open(BASEFILENAME, 'r')
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
    
    def getCost(self, datas):
        costDict = defaultdict(list)
        for key,values in datas.items():
            cost = 0
            for value in values:
                df = pd.read_csv('data/baselines/'+str(value)+'-costMonitor.csv')
                cost += df['avgCost'].iloc[-1]
            cost /= len(values)
            costDict[(key[0])] = cost # removed user count
        return costDict

entries = EntryLoader()
filteredDatas = entries.filter(cost_weight=[0])
costs = entries.getCost(filteredDatas)
print(costs)

net_weights = sorted(set(key[0] for key in costs.keys()))
print(net_weights)

palette = sns.color_palette("tab10")
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Adjust the bottom space
legend_entries = []

bar_width = .2  # Width of individual bars
gap_width = 0.1 # Width of the gap between groups
index = np.arange(len(net_weights)) * (bar_width + gap_width) 

baselines = 0
baselineLoader = BaseLineLoader()

for j, nw in enumerate(net_weights):
    for key, value in costs.items():
        if key[0] == nw :
            bar = ax.bar(index[j], value, bar_width, label=f'(α,β)=({nw},{1-nw})')

ax.set_ylabel('Cost/min')
plt.gca().set_xticks([])
plt.gca().set_xticklabels([])
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=len(net_weights)/2, fontsize='medium')

plt.tight_layout()
plt.savefig(f'thesis_plots/images/v2Total_CostsExceptCost2.png', dpi=300, bbox_inches='tight')