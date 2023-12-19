python3 v1Scheduler.py # if not default scheduler

python3 updateData.py
cd ../loadTest
python3 costMonitor.py
python3 queryCPUusage.py
locust --csv default_load_2500_8m --csv-full-history -u 2500 -r 100 -t 8m -H http://$(k get svc | grep frontend | grep Cluster | awk '{print $3}'):80 --headless



