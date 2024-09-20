from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/bookinfo/data')
USERS = [50,1000]

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
                df = pd.read_csv(str(value)+'_stats_history.csv')
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
                df = pd.read_csv(str(value)+'-costMonitor.csv')
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
    
    def getCost(self, datas):
        costDict = defaultdict(list)
        for key,values in datas.items():
            cost = 0
            for value in values:
                df = pd.read_csv(str(value)+'-costMonitor.csv')
                cost += df['avgCost'].iloc[-1]
            cost /= len(values)
            costDict[(key[0])] = cost # removed user count
        return costDict

    def getTotalRequests(self, datas):
        requestDict = defaultdict(int)
        for key, values in datas.items():
            request = 0
            for value in values:
                df = pd.read_csv(str(value)+'_stats_history.csv')
                df = df[df['Name'] == 'Aggregated']
                mn = df['Timestamp'].min()
                df.loc[:, ('Timestamp')] = df.loc[:, ('Timestamp')] - mn
                df = df[df['Timestamp'] > 20]
                request += df['Total Request Count'].max()
            request /= len(values) # take avg of all available data, if we run multiple benchmarks
            requestDict[key] = request
        return requestDict

entries = EntryLoader()
filteredDatas = entries.filter(userCount=USERS, cost_weight=[0.5], net_weight=[.25])
requests = entries.getTotalRequests(filteredDatas)

cw = sorted(set(key[2] for key in requests.keys()))[0]
nw = sorted(set(key[0] for key in requests.keys()))[0]

baselines = 3
baselineLoader = BaseLineLoader()
filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'], user=USERS)
baselinesRequest = baselineLoader.getTotalRequests(filteredBaselines)

palette = sns.color_palette("tab10")


fig, ax = plt.subplots(1, 1, figsize=(12,9))
plt.subplots_adjust(bottom=0.2)
legend_entries = []
bar_width = .2
group_width = bar_width * 4
gap_width = 0.05
index = np.arange(len(USERS)) * (group_width + gap_width) 

bars = {}

for i, user in enumerate(USERS):
    bardefault = ax.bar(index[i], baselinesRequest['default',user], bar_width, label='default', color=palette[-1])
    value = baselinesRequest['default',user]
    # ax.text(bardefault[0].get_x() + bardefault[0].get_width() / 2, bardefault[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=14, fontweight='bold')
    if value > 5000:
        ax.text(bardefault[0].get_x() + bardefault[0].get_width() / 2, bardefault[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')
    else:
        ax.text(bardefault[0].get_x() + bardefault[0].get_width() / 2, bardefault[0].get_height() , f' {(value/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=18, fontweight='bold')
    barNetMarks = ax.bar(index[i] + bar_width, baselinesRequest[('netmarks',user)], bar_width, label='NetMARKS', color=palette[-2])
    value = baselinesRequest[('netmarks',user)]
    if value > 5000:
        ax.text(barNetMarks[0].get_x() + barNetMarks[0].get_width() / 2, barNetMarks[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')
    else:
        ax.text(barNetMarks[0].get_x() + barNetMarks[0].get_width() / 2, barNetMarks[0].get_height() , f' {(value/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=18, fontweight='bold')
    # ax.text(barNetMarks[0].get_x() + barNetMarks[0].get_width() / 2, barNetMarks[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=14, fontweight='bold')
    barBinPack = ax.bar(index[i] + 2 * bar_width, baselinesRequest[('binpack',user)], bar_width, label='BinPacking', color=palette[-3])
    value = baselinesRequest[('binpack',user)]
    # ax.text(barBinPack[0].get_x() + barBinPack[0].get_width() / 2, barBinPack[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=14, fontweight='bold')
    if value > 5000:
        ax.text(barBinPack[0].get_x() + barBinPack[0].get_width() / 2, barBinPack[0].get_height() , f'{(value/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')
    else:
        ax.text(barBinPack[0].get_x() + barBinPack[0].get_width() / 2, barBinPack[0].get_height() , f' {(value/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=18, fontweight='bold')

    sameNetRequests = []
    for key, value in requests.items():
        if key[0] == nw and key[2] == cw and key[3] == user:
            sameNetRequests.append(value)
    bar = ax.bar(index[i] + 3 * bar_width, sameNetRequests, bar_width, label=f'MOS', color=palette[0])
    # ax.text(barMOS[0].get_x() + barMOS[0].get_width() / 2, barMOS[0].get_height() , f'{(sameNetRequests[0]/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=14, fontweight='bold')
    if sameNetRequests[0] > 5000:
        ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f'{(sameNetRequests[0]/1000):.1f}K ', rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')
    else:
        ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , f' {(sameNetRequests[0]/1000):.1f}K', rotation='vertical', ha='center', va='bottom', color='black', fontsize=18, fontweight='bold')
    
    if i == 0:
        legend_entries = [bardefault, barNetMarks, barBinPack, bar]

def convert_Request_count(x, pos):
    return f'{int(x//1000)}K'

xLabels = [f'N={x}' for x in USERS]
ax.set_xticks(index + 2*bar_width - bar_width/2)
ax.set_xticklabels(xLabels, fontsize=18)
ax.set_ylabel('$R_t$', fontsize=18)
ax.yaxis.set_major_formatter(FuncFormatter(convert_Request_count))

entries = EntryLoader()
filteredDatas = entries.filter(cost_weight=[.5], net_weight=[.25])
costs = entries.getCost(filteredDatas)

cost_weights = sorted(set(key[2] for key in costs.keys()))
net_weights = sorted(set(key[0] for key in costs.keys()))

fig.legend(handles=legend_entries,loc='upper center', bbox_to_anchor=(0.5, -0), ncol=len(legend_entries), fontsize=18)
plt.tight_layout()
plt.savefig(f'../thesis_plots/images/Rt_Baseline.png', dpi=300, bbox_inches='tight')

## COST PART
fig, ax = plt.subplots(1, 1, figsize=(12,9))
plt.subplots_adjust(bottom=0.2)
bar_width = .2
group_width = bar_width * len(cost_weights)
gap_width = 0.05 # Width of the gap between groups
index = np.arange(len(net_weights)) * (group_width + gap_width) 

baselines = 3
baselineLoader = BaseLineLoader()

filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'])
baselinesCosts = baselineLoader.getCost(filteredBaselines)
baseNames = ['default', 'netmarks', 'binpack']

def getCostString(x):
    if x - int(x) < .99:
        return f'{x:.2f}$ '
    else:
        return f'{x:.0f}$ '

for i, baseline in enumerate(baseNames):
    bar = ax.bar((bar_width+gap_width) * i, baselinesCosts[(baseline)], bar_width, label=baseline, color=palette[-i-1])
    ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , getCostString(baselinesCosts[(baseline)]) , rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')

for i, cw in enumerate(cost_weights):
    sameNetRequests = []
    for j, nw in enumerate(net_weights):
        for key, value in costs.items():
            if key[0] == nw and key[2] == cw:
                sameNetRequests.append(value)
    bar = ax.bar(baselines * (bar_width+gap_width) + index + i * bar_width, sameNetRequests, bar_width, label=f'Cost Weight {cw}', color=palette[i])
    ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() , getCostString(sameNetRequests[0]) , rotation='vertical', ha='center', va='top', color='white', fontsize=18, fontweight='bold')

ax.set_ylabel('$C$', fontsize=18)
xticks = [i * (bar_width+gap_width) for i in range(baselines)]
xticks.extend(baselines * (bar_width+gap_width) + index + group_width / 2 - bar_width / 2)
ax.set_xticks(xticks)
ax.set_xticklabels(['default', 'NetMARKS', 'BinPacking'] + [f'MOS' for weight in net_weights], fontsize=18)
ax.tick_params(axis='x')

# fig.legend(handles=legend_entries,loc='upper center', bbox_to_anchor=(0.5, -0), ncol=len(legend_entries), fontsize=18)
plt.tight_layout()
plt.savefig(f'../thesis_plots/images/C_Baseline.png', dpi=300, bbox_inches='tight')
# plt.savefig(f'thesis_plots/images/Rt_C_Baseline.svg', bbox_inches='tight')