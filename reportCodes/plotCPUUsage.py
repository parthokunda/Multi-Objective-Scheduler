import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

file_path = '1001-cpuUsage.csv'
data = pd.read_csv(file_path)

vm1_data = data[data['node_name'] == 'k8s-vm1']
vm2_data = data[data['node_name'] == 'k8s-vm2']

vm1_avg = vm1_data['value'].mean() / 4.0
vm2_avg = vm2_data['value'].mean() / 4.0

plt.figure(figsize=(5,3))
plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
bar1 = plt.barh('Node 1', vm1_avg, color='#6a0dad', label='Node 1')
bar2 = plt.barh('Node 2', vm2_avg, color='#008000', label='Node 2')
plt.xlabel('CPU Usage (%)', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.tight_layout()
plt.savefig('cpuUsage.png', dpi=300)
plt.savefig('cpuUsage.svg')