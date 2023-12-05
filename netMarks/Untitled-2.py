
import time
import schedule
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def your_task():
    print("Task Started")
    # Replace this with the task you want to execute every minute
    for i in range(100000):
        for i in range(2000):
            continue
    print("Task Done")

# schedule.every(5).seconds.do(your_task)

# Run the task every 1 minute indefinitely
while True:
    # your_task()
    # break
    # schedule.run_pending()
    # with ProcessPoolExecutor() as proc_executor:
    #     proc_executor.submit(your_task)
    #     time.sleep(5)
    with ThreadPoolExecutor() as thread_executor:
        thread_executor.submit(your_task)
        time.sleep(5)
# asyncio.run(your_task())
    # threading.Thread(target=your_task)
    # time.sleep(5)  # Sleep for 60 seconds (1 minute)