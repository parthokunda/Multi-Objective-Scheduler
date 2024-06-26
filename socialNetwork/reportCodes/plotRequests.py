import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/socialNetwork/loadTesting')

class EntryLoader :
    def __init__(self):
        file = open('entries1min.txt', 'r')
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
                df = pd.read_csv('data/'+str(value)+'_stats_history.csv')
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
        file = open('entries_baselines1min.txt', 'r')
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
                df = pd.read_csv('data/'+str(value)+'_stats_history.csv')
                df = df[df['Name'] == 'Aggregated']
                mn = df['Timestamp'].min()
                df.loc[:, ('Timestamp')] = df.loc[:, ('Timestamp')] - mn
                df = df[df['Timestamp'] > 20]
                request += df['Total Request Count'].max()
            request /= len(values) # take avg of all available data, if we run multiple benchmarks
            requestDict[key] = request
        return requestDict

USERFILTER =  50
entries = EntryLoader()
filteredDatas = entries.filter(userCount=[USERFILTER], cost_weight=[0,.25,.5,.75])
requests = entries.getTotalRequests(filteredDatas)

cost_weights = sorted(set(key[2] for key in requests.keys()))
net_weights = sorted(set(key[0] for key in requests.keys()))

palette = sns.color_palette("tab10")
fig, (ax,ax2) = plt.subplots(1, 2, figsize=(12,4))
plt.subplots_adjust(bottom=0.2)
legend_entries = []
bar_width = .2
group_width = bar_width * len(cost_weights)  # The total width of a group
gap_width = 0.05
index = np.arange(len(net_weights)) * (group_width + gap_width) 

for i, cw in enumerate(cost_weights):
    sameNetRequests = []
    for j, nw in enumerate(net_weights):
        for key, value in requests.items():
            if key[0] == nw and key[2] == cw:
                sameNetRequests.append(value)
    for j, nw in enumerate(net_weights):
        bar = ax.bar(index[j] + i * bar_width, sameNetRequests[j], bar_width, label=f'γ = {cw}', color=palette[i])
        if sameNetRequests[j] > 20000:
            ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{(sameNetRequests[j]/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
        else:
            ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f' {(sameNetRequests[j]/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=12, fontweight='bold')
    legend_entries.append(bar)

def RtToK(x,_):
    return f'{int(x//1000)}K'

ax.yaxis.set_major_formatter(FuncFormatter(RtToK))
ax.set_ylabel('$R_t$', fontsize=14)
xticks = []
xticks.extend(index + group_width / 2 - bar_width / 2)
ax.set_xticks(xticks)
ax.set_xticklabels([f'$𝛼_R$ = {weight}' for weight in net_weights], fontsize=12)
ax.set_title(f'User Count, $N$ = {USERFILTER}', fontsize=14)

USERFILTER =  1000
entries = EntryLoader()
filteredDatas = entries.filter(userCount=[USERFILTER], cost_weight=[0,.25,.5, .75])
requests = entries.getTotalRequests(filteredDatas)

cost_weights = sorted(set(key[2] for key in requests.keys()))
net_weights = sorted(set(key[0] for key in requests.keys()))

bar_width = .2
group_width = bar_width * len(cost_weights)  # The total width of a group
gap_width = 0.05
index = np.arange(len(net_weights)) * (group_width + gap_width) 

for i, cw in enumerate(cost_weights):
    sameNetRequests = []
    for j, nw in enumerate(net_weights):
        for key, value in requests.items():
            if key[0] == nw and key[2] == cw:
                sameNetRequests.append(value)
    for j, nw in enumerate(net_weights):
        bar = ax2.bar(index[j] + i * bar_width, sameNetRequests[j], bar_width, label=f'γ = {cw}', color=palette[i])
        if sameNetRequests[j] > 20000:
            ax2.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{(sameNetRequests[j]/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
        else:
            ax2.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f' {(sameNetRequests[j]/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=12, fontweight='bold')

ax2.yaxis.set_major_formatter(FuncFormatter(RtToK))
ax2.set_ylabel('$R_t$', fontsize=14)
xticks = []
xticks.extend(index + group_width / 2 - bar_width / 2)
ax2.set_xticks(xticks)
ax2.set_xticklabels([f'$𝛼_R$ = {weight}' for weight in net_weights], fontsize=12)
ax2.set_title(f'User Count, $N$ = {USERFILTER}', fontsize=14)

fig.legend(handles=legend_entries, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=len(cost_weights), fontsize=12)
plt.tight_layout()
plt.savefig(f'thesis_plots/images/Rt.png', dpi=300, bbox_inches='tight')
plt.savefig(f'thesis_plots/images/Rt.svg', bbox_inches='tight')