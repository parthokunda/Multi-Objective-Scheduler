import pandas as pd
import matplotlib.pyplot as plt

datalowdefault = pd.read_csv('netMarks_2500_2m_stats_history.csv')
datahighdefault = pd.read_csv('default_2500_2m_stats_history.csv')

datalowdefault = datalowdefault[datalowdefault['Name'] == 'Aggregated']
datahighdefault = datahighdefault[datahighdefault['Name'] == 'Aggregated']

start = datalowdefault['Timestamp'][0]
datalowdefault['Timestamp'] = datalowdefault['Timestamp'] - start
start = datahighdefault['Timestamp'][0]
datahighdefault['Timestamp'] = datahighdefault['Timestamp'] - start

datalowdefault = datalowdefault[datalowdefault['Requests/s'] > 0]
datahighdefault = datahighdefault[datahighdefault['Requests/s'] > 0]
# datalowdefault['Readable_Time'] = pd.to_datetime(datalowdefault['Timestamp'], unit='s')
# print(datalowdefault['Readable_Time'])

fig, axs = plt.subplots(2,2,figsize=(12,8))

axs[0,0].plot(datalowdefault['Timestamp'],datalowdefault['Requests/s'], label = 'NetMarks')
axs[0,0].plot(datahighdefault['Timestamp'],datahighdefault['Requests/s'], color='red', label = 'Default')
axs[0,0].grid(True)
axs[0,0].set_xlabel('Timestamp')
axs[0,0].set_ylabel('Requests/s')
axs[0,0].legend()

axs[0,1].plot(datalowdefault['Timestamp'],datalowdefault['99%'], label = 'NetMarks')
axs[0,1].plot(datahighdefault['Timestamp'],datahighdefault['99%'], color='red', label = 'Default')
axs[0,1].grid(True)
axs[0,1].set_xlabel('Timestamp')
axs[0,1].set_ylabel('99% Response Time')
axs[0,1].legend()

# plt.figure()
axs[1,0].plot(datalowdefault['Timestamp'], datalowdefault['Total Median Response Time'], linestyle='-', label = 'NetMarks')
axs[1,0].plot(datahighdefault['Timestamp'], datahighdefault['Total Median Response Time'], color='green', label = 'Default')
axs[1,0].grid(True)
# axs[0, 0].set_title('Graph 1')
axs[1,0].set_xlabel('Timestamp')
axs[1,0].set_ylabel('Median Response Time')
axs[1,0].legend()

axs[1,1].plot(datalowdefault['Timestamp'],datalowdefault['Total Request Count'], label = 'NetMarks')
axs[1,1].plot(datahighdefault['Timestamp'], datahighdefault['Total Request Count'], color='green', label = 'Default')
axs[1,1].grid(True)
axs[1,1].set_xlabel('Timestamp')
axs[1,1].set_ylabel('Total Request Count')
axs[1,1].legend()



# plt.show()
fig.suptitle("Default vs NetMarks - 2500user 100spawn 2minute")
plt.savefig('default-netmarks-highload.png')