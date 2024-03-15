import math
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/loadTest/')
USERS = [50,2000]
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
filteredDatas = entries.filter(userCount=USERS, cost_weight=[0], net_weight=[0])
requests = entries.getTotalRequests(filteredDatas)
net_weights = sorted(set(key[0] for key in requests.keys()))

baselines = 3
baselineLoader = BaseLineLoader()
filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'])
baselinesRequest = baselineLoader.getTotalRequests(filteredBaselines)

palette = sns.color_palette("tab10")
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12,4), gridspec_kw={'width_ratios': [5, 3]})
# plt.subplots_adjust(bottom=0.2)
legend_entries = []
bar_width = .2 
group_width = bar_width * (len(net_weights)+baselines)
gap_width = 0.1
index = np.arange(len(USERS)) * (group_width + gap_width) 

for i, user in enumerate(USERS):
    bar1 = ax.bar(index[i], baselinesRequest[('default',user)], bar_width, label='default', color=palette[-1])
    bar2 = ax.bar(index[i] + bar_width, baselinesRequest[('netmarks',user)], bar_width, label='netMarks', color=palette[-2])
    bar3 = ax.bar(index[i] + (bar_width) * 2, baselinesRequest[('binpack',user)], bar_width, label='binpack', color=palette[-3])
    ax.text(bar1[0].get_x() + bar1[0].get_width() / 2, bar1[0].get_height() , f"{baselinesRequest[('default',user)]/1000:.1f}K ", rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
    ax.text(bar2[0].get_x() + bar2[0].get_width() / 2, bar2[0].get_height() , f"{baselinesRequest[('netmarks',user)]/1000:.1f}K ", rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
    ax.text(bar3[0].get_x() + bar3[0].get_width() / 2, bar3[0].get_height() , f"{baselinesRequest[('binpack',user)]/1000:.1f}K ", rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
    if i == 0:
        legend_entries.extend([bar1,bar2,bar3])
    for key, value in requests.items():
        if key[0] == net_weights[0] and key[3] == user:
            bar = ax.bar(index[i] + (baselines) * bar_width, value, bar_width, label=f'(α,β)=({0},{1-0})', color=palette[0])
            ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{value/1000:.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')
            if i == 0:
                legend_entries.append(bar)

def RtToK(x,_):
    return f'{int(x//1000)}K'
ax.yaxis.set_major_formatter(FuncFormatter(RtToK))
ax.set_ylabel('$R_t$', fontsize=14)
xticks = []
xticks.extend(index + group_width / 2 - bar_width / 2)
ax.set_xticks(xticks)
ax.set_xticklabels( [f'N={user}' for user in USERS], fontsize=12)

### COST PART

entries = EntryLoader()
filteredDatas = entries.filter(cost_weight=[0], net_weight=[0])
costs = entries.getCost(filteredDatas)
bar_width = .2  # Width of individual bars
gap_width = 0.05 # Width of the gap between groups
group_width = bar_width + gap_width
index = np.arange(baselines + len(costs)) * (group_width) 

baselines = 3
baselineLoader = BaseLineLoader()

filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'])
baselinesCosts = baselineLoader.getCost(filteredBaselines)
palette = sns.color_palette("tab10")

bars = []
bar = ax2.bar(0, baselinesCosts[('default')], bar_width, label='default', color=palette[-1])
bars.append((bar, baselinesCosts[('default')]))
bar = ax2.bar(group_width, baselinesCosts[('netmarks')], bar_width, label='netMarks', color=palette[-2])
bars.append((bar, baselinesCosts[('netmarks')]))
bar = ax2.bar(group_width*2, baselinesCosts[('binpack')], bar_width, label='binpack', color=palette[-3])
bars.append((bar, baselinesCosts[('binpack')]))

for j, nw in enumerate(net_weights):
    for key, value in costs.items():
        if key[0] == nw :
            bar = ax2.bar(index[j+baselines], value, bar_width, label=f'(α,β)=({nw},{1-nw})')
            bars.append((bar,value))
def getCostNum(x):
    if x < 1:
        return f'{x:.1f}'
    else: return f'{x:.0f}'

for bar in bars:
    ax2.text(bar[0][0].get_x() + bar[0][0].get_width() / 2, bar[0][0].get_height() , f'{getCostNum(bar[1])}$ ', rotation='vertical', ha='center', va='top', color='white', fontsize=12, fontweight='bold')

ax2.set_ylabel('$C$', fontsize=14)
plt.gca().set_xticks([])
plt.gca().set_xticklabels([])

fig.legend(handles=legend_entries, loc='upper center', bbox_to_anchor=(0.5, -0.0), ncol=len(legend_entries), fontsize=12)

plt.tight_layout()
plt.savefig(f'thesis_plots/images/baseline_Rt_withoutGamma.png', dpi=1200, bbox_inches='tight')
plt.savefig(f'thesis_plots/images/baseline_Rt_withoutGamma.svg', bbox_inches='tight')