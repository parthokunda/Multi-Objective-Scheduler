import random
import string
from locust import HttpUser, task, between, events
import locust.stats
locust.stats.CSV_STATS_FLUSH_INTERVAL_SEC = 20
locust.stats.CSV_STATS_INTERVAL_SEC = 3


# Define a class inheriting from HttpUser
class SocialMediaUser(HttpUser):
    # Set a wait time between tasks
    wait_time = between(0, 0)

    # Initialize class with environment variables or default values
    def __init__(self, parent):
        super(SocialMediaUser, self).__init__(parent)
        self.max_user_index = 962  # Assuming an environment variable or a fixed value
        self.charset = list(string.ascii_letters + string.digits)
        self.decset = list(string.digits)

    # Generate a random string from the given charset
    def string_random(self, length):
        return ''.join(random.choice(self.charset) for _ in range(length))

    # Generate a random string of digits
    def dec_random(self, length):
        return ''.join(random.choice(self.decset) for _ in range(length))

    # Task for composing a post
    @task(1)
    def compose_post(self):
        user_index = random.randint(0, self.max_user_index - 1)
        username = "username_{}".format(user_index)
        user_id = str(user_index)
        text = self.string_random(256)
        num_user_mentions = random.randint(0, 5)
        num_urls = random.randint(0, 5)
        num_media = random.randint(0, 4)
        media_ids = '['

        for _ in range(num_user_mentions):
            user_mention_id = user_index
            while user_index == user_mention_id:
                user_mention_id = random.randint(0, self.max_user_index - 1)
            text += " @username_{}".format(user_mention_id)

        for _ in range(num_urls):
            text += " http://{}".format(self.string_random(64))

        for _ in range(num_media):
            media_id = self.dec_random(18)
            media_ids += "\"{}\",".format(media_id)

        media_ids = media_ids.rstrip(',') + ']'
        body = {
            "username": username,
            "user_id": user_id,
            "text": text,
            "media_ids": media_ids,
            "media_types": "[\"png\"]" * num_media,
            "post_type": "0"
        }
        self.client.post("/wrk2-api/post/compose", data=body)

    # Task for reading user timeline
    @task(3)
    def read_user_timeline(self):
        user_id = str(random.randint(0, self.max_user_index - 1))
        start = str(random.randint(0, 100))
        stop = str(int(start) + 10)
        self.client.get("/wrk2-api/user-timeline/read?user_id={}&start={}&stop={}".format(user_id, start, stop))

    # Task for reading home timeline
    @task(6)
    def read_home_timeline(self):
        user_id = str(random.randint(0, self.max_user_index - 1))
        start = str(random.randint(0, 100))
        stop = str(int(start) + 10)
        self.client.get("/wrk2-api/home-timeline/read?user_id={}&start={}&stop={}".format(user_id, start, stop))


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