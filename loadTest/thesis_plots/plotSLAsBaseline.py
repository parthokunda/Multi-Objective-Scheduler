import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from collections import defaultdict
os.chdir('/root/loadTest/')
USERS = [50,1000,2000]
FILENAME = 'entries2.txt'
BASEFILENAME = 'entries_baselines2.txt'

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
    
    def getSLA(self, datas:defaultdict(list), slaLimits):
        slaPercents = defaultdict(list)
        for key,values in datas.items():
            slas = []
            for value in values:
                slas.append(pd.read_csv('data/hpdc/'+str(value)+'-SLA.csv'))
            for limitIndex, limit in enumerate(slaLimits):
                percentage = 0
                for i, value in enumerate(values):
                    percentage += (slas[i]['response_time'] > limit).sum() / len(slas[i]) * 100
                percentage /= len(values)
                slaPercents[key].append(percentage)
        return slaPercents

class BaseLineLoader :
    def __init__(self):
        file = open(BASEFILENAME, 'r')
        lines = file.readlines()
        self.datas = defaultdict(list)
        for i, line in enumerate(lines):
            line = eval(line)
            self.datas[line['baseline'], line['user']].append(line['fileNum'])
    
    def filter(self, baseline:list = None, user:list = None):
        filterData = defaultdict(list)
        for key, values in self.datas.items():
            if ((baseline is None or key[0] in baseline) and
               (user is None or key[1] in user)):
                filterData[key] = values
        return filterData
    
    def getSLA(self, datas:defaultdict(list), slaLimits):
        slaPercents = defaultdict(list)
        for key,values in datas.items():
            slas = []
            for value in values:
                slas.append(pd.read_csv('data/baselines/'+str(value)+'-SLA.csv'))
            for limitIndex, limit in enumerate(slaLimits):
                percentage = 0
                for i, value in enumerate(values):
                    percentage += (slas[i]['response_time'] > limit).sum() / len(slas[i]) * 100
                percentage /= len(values)
                slaPercents[key].append(percentage)
        return slaPercents


plt.rcParams.update({'font.size': 14})
fig, axs = plt.subplots(1,3, figsize=(30,10))
palette = sns.color_palette("tab10")
slaLimits = np.linspace(2000, 6000, 100)
slaUps = [500, 5000, 6000]
slaDowns = [0, 1000, 2000]

entries = EntryLoader()
filteredDatas = entries.filter(userCount=USERS, net_weight=[.25], cost_weight=[.5])
print(filteredDatas)
nw = .25
cw = .5

baselineLoader = BaseLineLoader()
filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks', 'binpack'],user=USERS)
print(filteredBaselines)

for i, user in enumerate(USERS):
    slaLimits = np.linspace(slaDowns[i], slaUps[i], 100)
    slaDict = entries.getSLA(filteredDatas, slaLimits)
    baseSlaDict = baselineLoader.getSLA(filteredBaselines, slaLimits)
    axs[i].plot(slaLimits, slaDict[(nw, 1-nw, cw, user)], label='CMAS', color=palette[0], linewidth=3)
    axs[i].plot(slaLimits, baseSlaDict[('default', user)], label='default', linewidth=3, color=palette[-1])
    axs[i].plot(slaLimits, baseSlaDict[('netmarks', user)], label='netmarks', linewidth=3, color=palette[-2])
    axs[i].plot(slaLimits, baseSlaDict[('binpack', user)], label='binpack', linewidth=3, color=palette[-3])
    if i == 0:
        axs[i].set_ylabel("SLA Violation (%)", fontsize='xx-large')
    axs[i].tick_params(axis='x', labelrotation=45, labelsize='xx-large')
    axs[i].tick_params(axis='y', labelsize='xx-large')
    # axs[i].legend(fontsize='xx-large')
    axs[i].set_title(f'σ={user}', fontsize='xx-large')
    # axs[i].set_xlabel(f'CMAS', fontsize='xx-large')


# print(len(slaLimits), len(slaDict[('netmarks', USERFILTER)]), len(slaDict[('default', USERFILTER)]))
# for ax in axs:
#     ax.set_ylabel("Violation (in %)", fontsize="xx-large")
#     ax.tick_params(axis='x', labelrotation=45, labelsize="xx-large")
#     ax.tick_params(axis='y', labelsize="xx-large")
#     ax.legend(fontsize='xx-large')

def add_ms(x, pos):
    return f'{int(x)/1000} s'

# Apply the formatter to each Axes object
from matplotlib.ticker import FuncFormatter
for ax in axs:
    ax.xaxis.set_major_formatter(FuncFormatter(add_ms))
handles, labels = axs[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.1), fontsize='xx-large')

plt.tight_layout()
plt.savefig(f'thesis_plots/images/v2_Baseline_SLAs_Combined.png', dpi=300, bbox_inches='tight')
