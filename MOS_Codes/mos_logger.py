import logging as logs

logs.basicConfig(
    filename="mos_scheduler_logs.txt", level=logs.INFO, 
    filemode='w',
    format='%(asctime)s - %(levelname)s  [%(filename)s:%(lineno)d] - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S')

# Create a logger object
mos_logger = logs.getLogger(__name__)