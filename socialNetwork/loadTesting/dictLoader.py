from collections import defaultdict

def loadEntries():
    file = open('entries.txt', 'r')
    lines = file.readlines()
    datas = defaultdict(list)
    datasDict = []
    for line in lines:
        line = eval(line)
        weights = (line['net_weight'], line['cpu_weight'], line['cost_weight'], line['userCount'])
        datas[weights].append(line['fileNum'])
    return datas

datas = loadEntries()
print(datas[(0,0,1,2000)])
files_halfCPU = [values for key,values in datas.items() if key[1] == .5 for value in values]
print([value for value ])