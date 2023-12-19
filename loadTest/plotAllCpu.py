import pandas as pd
import matplotlib.pyplot as plt

nMCPU = pd.read_csv('netMarks_load_2500_5m_cpuUsage.csv')
v1CPU = pd.read_csv('v1_load_2500_5m_cpuUsage.csv')

nM_start = nMCPU['timestamp'].min()
v1_start = v1CPU['timestamp'].min()

nMCPU['timestamp'] = nMCPU['timestamp'] - nM_start
v1CPU['timestamp'] = v1CPU['timestamp'] - v1_start

nMvm1 = nMCPU[nMCPU['node_name'] == 'k8s-vm1']
nMvm2 = nMCPU[nMCPU['node_name'] == 'k8s-vm2']
nMvm3 = nMCPU[nMCPU['node_name'] == 'k8s-vm3']

v1vm1 = v1CPU[nMCPU['node_name'] == 'k8s-vm1']
v1vm2 = v1CPU[nMCPU['node_name'] == 'k8s-vm2']
v1vm3 = v1CPU[nMCPU['node_name'] == 'k8s-vm3']


# datalowdefault = datalowdefault[datalowdefault['Requests/s'] > 0]
# datahighdefault = datahighdefault[datahighdefault['Requests/s'] > 0]
# # datalowdefault['Readable_Time'] = pd.to_datetime(datalowdefault['Timestamp'], unit='s')
# # print(datalowdefault['Readable_Time'])

fig, axs = plt.subplots(3,1,figsize=(12,8))

axs[0].plot(nMvm1['timestamp'],nMvm1['value'], label = 'NetMarks')
axs[0].plot(v1vm1['timestamp'],v1vm1['value'], color='red', label = 'v1')
axs[0].grid(True)
axs[0].set_xlabel('Timestamp')
axs[0].set_ylabel('k8s-vm1')
axs[0].legend()

axs[1].plot(nMvm2['timestamp'],nMvm2['value'], label = 'NetMarks')
axs[1].plot(v1vm2['timestamp'],v1vm2['value'], color='red', label = 'v1')
axs[1].grid(True)
axs[1].set_xlabel('Timestamp')
axs[1].set_ylabel('k8s-vm2')
axs[1].legend()


axs[2].plot(nMvm3['timestamp'], nMvm3['value'], linestyle='-', label = 'NetMarks')
axs[2].plot(v1vm3['timestamp'], v1vm3['value'], color='red', label = 'v1')
axs[2].grid(True)
axs[2].set_xlabel('Timestamp')
axs[2].set_ylabel('k8s-vm3')
axs[2].legend()




# # plt.show()
fig.suptitle("v1 vs NetMarks CPU usage - 2500user 100spawn 5minute")
plt.savefig('v1 vs NetMarks CPU usage - 2500user 100spawn 5minute.png')