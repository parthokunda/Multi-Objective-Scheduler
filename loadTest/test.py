import matplotlib.pyplot as plt
import numpy as np

# Sample data
labels = ['Label1', 'Label2', 'Label3', 'Label4', 'Label5']
data1 = np.array([10, 15, 7, 12, 9])
data2 = np.array([8, 11, 5, 10, 7])
data3 = np.array([12, 14, 9, 11, 8])

# Set up the bar positions
bar_width = 0.25
index = np.arange(len(labels))

# Plotting the grouped bars for each label
plt.bar(index, data1, width=bar_width, label='Data 1')
plt.bar(index + 1 * bar_width, data2, width=bar_width, label='Data 2')
plt.bar(index + 2 * bar_width, data3, width=bar_width, label='Data 3')

# Adding labels and title
plt.xlabel('Labels')
plt.ylabel('Values')
plt.title('Grouped Bar Chart for Data1, Data2, Data3')
plt.xticks(index + bar_width, labels)
plt.legend()

# Show the plot
plt.savefig('test.png')
print(index)
