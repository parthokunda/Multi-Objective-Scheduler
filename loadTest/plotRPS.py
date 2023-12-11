import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('second_stats_history.csv')

data = data[data['Name'] == 'Aggregated']

start = data['Timestamp'][0]
data['Timestamp'] = data['Timestamp'] - start

data = data[data['Requests/s'] > 0]
# data['Readable_Time'] = pd.to_datetime(data['Timestamp'], unit='s')
# print(data['Readable_Time'])

fig, axs = plt.subplots(2,2,figsize=(12,8))

# plt.figure()
axs[1,0].plot(data['Timestamp'], data['Total Median Response Time'], linestyle='-')
axs[1,0].grid(True)
# axs[0, 0].set_title('Graph 1')
axs[1,0].set_xlabel('Timestamp')
axs[1,0].set_ylabel('Median Response Time')

axs[1,1].plot(data['Timestamp'],data['Total Average Response Time'])
axs[1,1].grid(True)
axs[1,1].set_xlabel('Timestamp')
axs[1,1].set_ylabel('Average Response Time')

axs[0,0].plot(data['Timestamp'],data['Requests/s'])
axs[0,0].grid(True)
axs[0,0].set_xlabel('Timestamp')
axs[0,0].set_ylabel('Requests/s')

axs[0,1].plot(data['Timestamp'],data['Failures/s'])
axs[0,1].grid(True)
axs[0,1].set_xlabel('Timestamp')
axs[0,1].set_ylabel('Failures/s')

# plt.show()
plt.savefig('rps.png')