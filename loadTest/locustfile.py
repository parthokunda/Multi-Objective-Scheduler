import random
from locust import HttpUser, TaskSet, between, constant, task, events
import locust.stats
locust.stats.CSV_STATS_FLUSH_INTERVAL_SEC = 20
locust.stats.CSV_STATS_INTERVAL_SEC = 3

products = [
    '0PUK6V6EV0',
    '1YMWWN1N4O',
    '2ZYFJ3GM2N',
    '66VCHSJNUP',
    '6E92ZMYYFZ',
    '9SIQT8TOJO',
    'L9ECAV7KIM',
    'LS4PSXUNUM',
    'OLJCESPC7Z']

def index(l):
    l.client.get("/", context = {"type": "index"})

def setCurrency(l):
    currencies = ['EUR', 'USD', 'JPY', 'CAD']
    l.client.post("/setCurrency",
        {'currency_code': random.choice(currencies)}, context={"type":"setCurrency"})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products), context={"type": "browseProduct"})

def viewCart(l):
    l.client.get("/cart", context={"type": "viewCart"})

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product, context={"type": "addToCartGet"})
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.choice([1,2,3,4,5,10])}, context={"type": "addToCartPost"})

def checkout(l):
    addToCart(l)
    l.client.post("/cart/checkout", {
        'email': 'someone@example.com',
        'street_address': '1600 Amphitheatre Parkway',
        'zip_code': '94043',
        'city': 'Mountain View',
        'state': 'CA',
        'country': 'United States',
        'credit_card_number': '4432-8015-6152-0454',
        'credit_card_expiration_month': '1',
        'credit_card_expiration_year': '2039',
        'credit_card_cvv': '672',
    }, context={"type":"checkout"})

class UserBehavior(TaskSet):

    def on_start(self):
        index(self)

    tasks = {index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1
        }

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = constant(0)

csvfile = None

@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response,
                       context, exception, start_time, url, **kwargs):
    if exception:
        print('Could not reach')
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