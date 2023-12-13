import pandas as pd
import matplotlib.pyplot as plt

nM = pd.read_csv('netMarks_load_2500_5m_stats_history.csv')
v1 = pd.read_csv('v1_load_2500_5m_stats_history.csv')

nM = nM[nM['Name'] == 'Aggregated']
v1 = v1[v1['Name'] == 'Aggregated']

nM_start = nM['Timestamp'].min()
v1_start = v1['Timestamp'].min()

nM['Timestamp'] = nM['Timestamp'] - nM_start
v1['Timestamp'] = v1['Timestamp'] - v1_start



fig, axs = plt.subplots(2,2,figsize=(12,8))

axs[0,0].plot(nM['Timestamp'],nM['Requests/s'], label = 'NetMarks')
axs[0,0].plot(v1['Timestamp'],v1['Requests/s'], color='red', label = 'v1')
axs[0,0].grid(True)
axs[0,0].set_xlabel('Timestamp')
axs[0,0].set_ylabel('Requests/s')
axs[0,0].legend()

axs[0,1].plot(nM['Timestamp'],nM['99%'], label = 'NetMarks')
axs[0,1].plot(v1['Timestamp'],v1['99%'], color='red', label = 'v1')
axs[0,1].grid(True)
axs[0,1].set_xlabel('Timestamp')
axs[0,1].set_ylabel('99% Response Time')
axs[0,1].legend()

# plt.figure()
axs[1,0].plot(nM['Timestamp'], nM['Total Median Response Time'], linestyle='-', label = 'NetMarks')
axs[1,0].plot(v1['Timestamp'], v1['Total Median Response Time'], color='red', label = 'v1')
axs[1,0].grid(True)
# axs[0, 0].set_title('Graph 1')
axs[1,0].set_xlabel('Timestamp')
axs[1,0].set_ylabel('Median Response Time')
axs[1,0].legend()

axs[1,1].plot(nM['Timestamp'],nM['Total Request Count'], label = 'NetMarks')
axs[1,1].plot(v1['Timestamp'], v1['Total Request Count'], color='red', label = 'v1')
axs[1,1].grid(True)
axs[1,1].set_xlabel('Timestamp')
axs[1,1].set_ylabel('Total Request Count')
axs[1,1].legend()



# plt.show()
fig.suptitle("v1 vs NetMarks - 2500user 100spawn 5minute")
plt.savefig('v1 vs NetMarks Network Stat - 2500user 100spawn 5minute.png')