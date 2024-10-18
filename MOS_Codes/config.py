import yaml

SCHEDULER_DATABASE_DIR = '/root/bookinfo/bench/data.db'
LOCAL_NODE_SCORE = 0.5
CLOUD_NODE_SCORE = 1.0
SHUFFLE_NODE_FOR_RANDOM_SCHEDULING = True
SCHEDULER_NAME = 'netMarksScheduler'

with open('config-scheduler.yaml') as yamlFile:
    yamlConfig = yaml.load(yamlFile, Loader=yaml.FullLoader)