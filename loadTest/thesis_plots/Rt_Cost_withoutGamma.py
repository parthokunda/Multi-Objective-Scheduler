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
    
    def getTotalRequests(self, datas):
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
    
    def getTotalRequests(self, datas):
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
filteredDatas = entries.filter(userCount=USERS, cost_weight=[0])
requests = entries.getTotalRequests(filteredDatas)

net_weights = sorted(set(key[0] for key in requests.keys()))

palette = sns.color_palette("tab10")
fig, (ax1,ax2) = plt.subplots(1, 2, figsize=(12,4), gridspec_kw={'width_ratios': [5, 2]})
plt.subplots_adjust(bottom=0.2)  # Adjust the bottom space
legend_entries = []
bar_width = .2  # Width of individual bars
group_width = bar_width * len(net_weights)  # The total width of a group
gap_width = 0.1 # Width of the gap between groups
index = np.arange(len(USERS)) * (group_width + gap_width) 

baselines = 0
baselineLoader = BaseLineLoader()

for j, nw in enumerate(net_weights):
    for i, user in enumerate(USERS):
        for key, value in requests.items():
            if key[0] == nw and key[3] == user:
                bar = ax1.bar(index[i] + j * bar_width, value, bar_width, label=f'(α,β)=({nw},{1-nw})', color=palette[j])
                ax1.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
                if i == 0:
                    legend_entries.append(bar)

def RtToK(x,_):
    return f'{int(x//1000)}K'
ax1.yaxis.set_major_formatter(FuncFormatter(RtToK))
ax1.set_ylabel('$R_t$', fontsize=14)
xticks = []
xticks.extend(index + group_width / 2 - bar_width / 2)
ax1.set_xticks(xticks)
ax1.set_xticklabels( [f'N={user}' for user in USERS])

entries = EntryLoader()
filteredDatas = entries.filter(cost_weight=[0])
costs = entries.getCost(filteredDatas)
net_weights = sorted(set(key[0] for key in costs.keys()))

bar_width = .2  # Width of individual bars
gap_width = 0.05 # Width of the gap between groups
index = np.arange(len(net_weights)) * (bar_width + gap_width) 

def getCostString(x):
    if x - int(x) < .99:
        return f'{x:.1f}$ '
    else:
        return f'{x:.0f}$ '
        
for j, nw in enumerate(net_weights):
    for key, value in costs.items():
        if key[0] == nw :
            bar = ax2.bar(index[j], value, bar_width, label=f'(α,β)=({nw},{1-nw})')
            ax2.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{getCostString(value)}', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')

ax2.set_ylabel('$C$', fontsize=14)
plt.gca().set_xticks([])
plt.gca().set_xticklabels([])

fig.legend(handles=legend_entries, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5, fontsize=13)
plt.tight_layout()
plt.savefig(f'thesis_plots/images/Rt_C_withoutGamma.png', dpi=1200, bbox_inches='tight')
plt.savefig(f'thesis_plots/images/Rt_C_withoutGamma.svg', bbox_inches='tight')