import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/socialNetwork/loadTesting')
USERS = [50]
FILENAME = 'entries1min.txt'
BASEFILENAME = 'entries_baselines1min.txt'
CMAS_COST_WEIGHT = 0.25
CMAS_NET_WEIGHT = 0.25

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
                print(value)
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

entries = EntryLoader()
filteredDatas = entries.filter(userCount=USERS, cost_weight=[CMAS_COST_WEIGHT], net_weight=[CMAS_NET_WEIGHT])
requests = entries.getTotalRequests(filteredDatas)

cw = sorted(set(key[2] for key in requests.keys()))[0]
nw = sorted(set(key[0] for key in requests.keys()))[0]
print(nw,cw)

baselines = 3
baselineLoader = BaseLineLoader()
filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'], user=USERS)
baselinesRequest = baselineLoader.getTotalRequests(filteredBaselines)

palette = sns.color_palette("tab10")
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Adjust the bottom space
legend_entries = []
bar_width = .2  # Width of individual bars
group_width = bar_width * 5  # The total width of a group
gap_width = 0.3 # Width of the gap between groups
index = np.arange(len(USERS)) * (group_width + gap_width) 
print(index)

print(baselinesRequest)

for i, user in enumerate(USERS):
    bardefault = ax.bar(index[i], baselinesRequest['default',user], bar_width, label='default', color=palette[-1])
    barNetMarks = ax.bar(index[i] + bar_width, baselinesRequest[('netmarks',user)], bar_width, label='netMarks', color=palette[-2])
    barBinPack = ax.bar(index[i] + 2 * bar_width, baselinesRequest[('binpack',user)], bar_width, label='binPack', color=palette[-3])
    # barDefault2N = ax.bar(index[i] + 3 * bar_width, baselinesRequest[('default2N',user)], bar_width, label='default2N', color=palette[-4])

    sameNetRequests = []
    for key, value in requests.items():
        if key[0] == nw and key[2] == cw and key[3] == user:
            sameNetRequests.append(value)
    print(user, sameNetRequests)
    barCMAS = ax.bar(index[i] + baselines * bar_width, sameNetRequests, bar_width, label=f'CMAS', color=palette[0])
    
    if i == 0:
        legend_entries = [bardefault, barNetMarks, barBinPack, barCMAS]

from matplotlib.ticker import FuncFormatter
def convert_Request_count(x, pos):
    return f'{int(x//1000)}K'

xLabels = [f'N={x}' for x in USERS]
ax.set_xticks(index + 2*bar_width - bar_width/2)
ax.set_xticklabels(xLabels)
ax.set_ylabel('R_t')
ax.yaxis.set_major_formatter(FuncFormatter(convert_Request_count))
ax.legend(handles=legend_entries,loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=4, fontsize='medium')

plt.tight_layout()
plt.savefig(f'thesis_plots/images/Social_Network_Baseline_Total_Requests_Combined_{USERS[0]}User.png', dpi=300, bbox_inches='tight')