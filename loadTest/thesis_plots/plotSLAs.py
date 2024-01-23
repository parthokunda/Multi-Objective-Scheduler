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
        file = open('entries_baselines.txt', 'r')
        lines = file.readlines()
        self.datas = defaultdict(list)
        for i, line in enumerate(lines):
            if i >= 12:
                break
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


markers = ['o', 's', '^', 'D', '*', 'p', 'v', '<', '>', 'H', '+', 'x']
plt.rcParams.update({'font.size': 14})
fig, axs = plt.subplots(1,5, figsize=(50,10))
palette = sns.color_palette("tab10")
slaLimits = np.linspace(1000, 5000, 100)

entries = EntryLoader()
filteredDatas = entries.filter(userCount=[1000])
slaDict = entries.getSLA(filteredDatas, slaLimits)
for i,nw in enumerate([0, .25, .5, .75, 1]):
    cost_weights = sorted(set(key[0] for key in slaDict.keys() if key[0] <= .51))
    for cwindex, cw in enumerate(cost_weights):
        axs[i].plot(slaLimits, slaDict[(nw, 1-nw, cw, 1000)], label=cw, color=palette[cwindex], linewidth=3)
        axs[i].set_ylabel("Violation (in %)", fontsize='xx-large')
        axs[i].tick_params(axis='x', labelrotation=45, labelsize='xx-large')
        axs[i].tick_params(axis='y', labelsize='xx-large')
    axs[i].legend(fontsize='xx-large')
    axs[i].set_xlabel(f'Network Weight = {nw}', fontsize='xx-large')

baselineLoader = BaseLineLoader()
filteredBaselines = baselineLoader.filter(baseline=['default', 'netmarks'],user=[1000])
slaDict = baselineLoader.getSLA(filteredBaselines, slaLimits)

for ax in axs:
    ax.plot(slaLimits, slaDict[('default', 1000)], label='default', linewidth=3, color=palette[-1])
    ax.plot(slaLimits, slaDict[('netmarks', 1000)], label='netmarks', linewidth=3, color=palette[-2])
    ax.set_ylabel("Violation (in %)", fontsize="xx-large")
    ax.tick_params(axis='x', labelrotation=45, labelsize="xx-large")
    ax.tick_params(axis='y', labelsize="xx-large")
    ax.legend(fontsize='xx-large')

def add_ms(x, pos):
    return f'{int(x)/1000} s'

# Apply the formatter to each Axes object
from matplotlib.ticker import FuncFormatter
for ax in axs:
    ax.xaxis.set_major_formatter(FuncFormatter(add_ms))
fig.suptitle("SLA Violation Graph", fontsize=28)
plt.tight_layout()
plt.savefig('thesis_plots/images/SLAs_1000userV1.png')
