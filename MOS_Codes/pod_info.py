import utils
def eventObj_to_totalRequests(eventObj):
    total_CPU = 0
    total_Memory = 0
    for container in eventObj['object'].spec.containers:
        cpu = container.resources.requests['cpu']
        memory = container.resources.requests['memory']
        total_CPU += utils.convertCPUData(cpu)
        total_Memory += utils.convertMemoryData(memory)
    return total_CPU, total_Memory