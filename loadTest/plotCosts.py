import pandas as pd
import matplotlib.pyplot as plt

dfs = []
files = [12,13,14,15,16,17,18]
labels = ['0', '.25', '.5', '.75', '1', '.125', '.375']

for file in files:
    dfs.append(pd.read_csv('data/'+str(file)+'-costMonitor.csv'))

cost = []
for df in dfs:
    cost.append(df['avgCost'].iloc[-1])

# for i, df in enumerate(dfs):
#     plt.plot(df['totalTime'], df['totalCost'], label=labels[i], marker = i)

plt.bar(labels, cost)
plt.title("Cost on avg")
plt.savefig("images/2_Cost on avg")