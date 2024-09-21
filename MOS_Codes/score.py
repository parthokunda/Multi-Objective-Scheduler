import utils
from mos_logger import logs

# return a normalized version of costing
def nodeCostScore(nodeList) -> dict[str, float]:
    local_nodes, cloud_nodes = utils.get_node_location(logs)
    running_nodes = utils.getRunningNodes(logs)
    costScores : dict[str,float] = {}

    for node in nodeList:
        if node in running_nodes:
            costScores[node] = 0.0
        else:
            if node in local_nodes:
                costScores[node] = 0.5
            elif node in cloud_nodes:
                costScores[node] = 1.0
            else:
                logs.error(f"node not found anywhere {node}")
            logs.debug(f'{node} has cost: {costScores[node]}')
    
    mx = max(costScores.values()) + .00001
    mn = min(costScores.values()) 
    logs.debug(f'Before normalization cost: {costScores}')
    for node in nodeList:
        costScores[node] = (costScores[node] - mn) / (mx - mn)
    logs.debug(f'Cost Score Normalized: {costScores}')
    return costScores