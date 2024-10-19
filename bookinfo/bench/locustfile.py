import random
from locust import HttpUser, TaskSet, between, constant, task, events
import locust.stats
locust.stats.CSV_STATS_FLUSH_INTERVAL_SEC = 20
locust.stats.CSV_STATS_INTERVAL_SEC = 3

def index(l):
    l.client.get("/productpage?u=normal", context = {"type": "index"})
def indexusertest(l):
    l.client.get("/productpage?u=test", context = {"type": "index"})

class UserBehavior(TaskSet):
    def on_start(self):
        index(self)
    tasks = {index: 1,
             indexusertest:1}

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = constant(0)

csvfile = None
ErrorMsgCount = 0

@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response,
                       context, exception, start_time, url, **kwargs):
    if exception:
        global ErrorMsgCount
        if ErrorMsgCount == 0:
            print('Could not reach')
            ErrorMsgCount += 1
    else:
        csvfile.write(f'{str(request_type)},{str(context["type"])},{str(name)},{str(response_time)}\n')

@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--csv-number", type=int, default="-1")

@events.test_start.add_listener
def _(environment, **kw):
    global csvfile
    if environment.parsed_options.csv_number == -1:
        csvfile = open(f'dbSetup-SLA.csv', 'w')
    else:
        csvfile = open(f'{environment.parsed_options.csv_number}-SLA.csv', 'w')
    csvfile.write(f'request_type,request_context,name,response_time\n')

@events.quitting.add_listener
def _(environment):
    csvfile.close()
