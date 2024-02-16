import string
import random
from locust import HttpUser, TaskSet, constant, events
import locust.stats
locust.stats.CSV_STATS_FLUSH_INTERVAL_SEC = 20
locust.stats.CSV_STATS_INTERVAL_SEC = 3

max_user_index = 962
charset = list(string.ascii_letters + string.digits)
decset = list(string.digits)

def string_random(length):
    return ''.join(random.choice(charset) for _ in range(length))

# Generate a random string of digits
def dec_random(length):
    return ''.join(random.choice(decset) for _ in range(length))

def index(l):
    l.client.get("/", context = {"type": "index"}, name="index")

def read_user_timeline(l):
    user_id = str(random.randint(0, max_user_index - 1))
    start = str(random.randint(0, 100))
    stop = str(int(start) + 10)
    l.client.get("/wrk2-api/user-timeline/read?user_id={}&start={}&stop={}".format(user_id, start, stop), name="read_user_timeline", context={"type": "read_user_timeline"})

def read_home_timeline(l):
    user_id = str(random.randint(0, max_user_index - 1))
    start = str(random.randint(0, 100))
    stop = str(int(start) + 10)
    l.client.get("/wrk2-api/home-timeline/read?user_id={}&start={}&stop={}".format(user_id, start, stop), name="read_home_timeline", context={"type": "read_home_timeline"})

def compose_post(l):
    user_index = random.randint(0, max_user_index - 1)
    username = "username_{}".format(user_index)
    user_id = str(user_index)
    text = string_random(256)
    num_user_mentions = random.randint(0, 5)
    num_urls = random.randint(0, 5)
    num_media = random.randint(0, 4)
    media_ids = '['

    for _ in range(num_user_mentions):
        user_mention_id = user_index
        while user_index == user_mention_id:
            user_mention_id = random.randint(0, max_user_index - 1)
        text += " @username_{}".format(user_mention_id)

    for _ in range(num_urls):
        text += " http://{}".format(string_random(64))

    for _ in range(num_media):
        media_id = dec_random(18)
        media_ids += "\"{}\",".format(media_id)

    media_ids = media_ids.rstrip(',') + ']'
    media_types = "["
    for i in range(num_media):
        if i < num_media-1:
            media_types += '\"png\",'
        else:
            media_types += '\"png\"'
    media_types += ']'

    body = {
        "username": username,
        "user_id": user_id,
        "text": text,
        "media_ids": media_ids,
        "media_types": media_types,
        "post_type": "0"
    }

    l.client.post("/wrk2-api/post/compose", data=body, name="compose_post", context={"type": "compose_post"})

class UserBehavior(TaskSet):
    def on_start(self):
        index(self)
    tasks = {
        read_home_timeline : 6,
        read_user_timeline : 3,
        compose_post : 1,
    }

class WebsiteUser(HttpUser):
    host = "http://10.107.157.87:8080"
    wait_time = constant(0)
    tasks = [UserBehavior]


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
    parser.add_argument("--csv-number", type=int, default="1")

@events.test_start.add_listener
def _(environment, **kw):
    global csvfile
    csvfile = open(f'{environment.parsed_options.csv_number}-SLA.csv', 'w')
    csvfile.write(f'request_type,request_context,name,response_time\n')

@events.quitting.add_listener
def _(environment):
    csvfile.close()