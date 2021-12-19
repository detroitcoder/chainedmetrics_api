import os
import csv
import pytest

from dateutil import parser
from app.markets import get_markets



from app import create_app
from app.models import db, Market
from flask_migrate import Migrate, command

config_dict = dict(
    MAILCHIMP_URL = 'https://na.com',
    MAILCHIMP_LIST = 'NA',
    MAILCHIMP_API_KEY = 'NA',
    DEVELOPMENT = True,
    DEBUG = True,
    DB_HOST = 'NA',
    DB_USER = 'NA',
    DB_PORT = 123,
    DATABASE = 'metrics',
    DB_PASS = 'NA',
    JWT_SECRET_KEY = 'NA',
    JWT_TOKEN_LOCATION = "headers",
    URL = 'https://dev.chainedmetrics.com',
    SQLALCHEMY_DATABASE_URI = f'sqlite:///:memory:',
)

@pytest.fixture
def client():
    
    app = create_app(config_dict)
    m = Migrate(app)
    db.init_app(app)
    with app.app_context():
        command.upgrade(m.get_config(), 'head')
        for market in get_test_markets():
            db.session.add(market)
        db.session.commit()

    with app.test_client() as client:
        yield client

def test_basic_request(client):
    """Request markets"""

    resp = client.get('/markets/')

    for k in ('ticker', 'fiscal_period', 'id', 'metric', 'value', 'value_string', 'broker_address'):
        for m in resp.json['markets']:
            assert k in m, f'{k} is missing from {m}'

def test_missing_broker_address_are_skipped(client):
    """Ensure that the test case for "AMZN/Q322/R" is not returned by
     the markets call because the broker address is missing
     """

    resp = client.get('/markets/')

    assert len(resp.json['markets']) == 3, 'Three markets are expected'
    for m in resp.json['markets']:
        assert m['metric_symbol'] != "AMZN/Q322/R"

def test_market_resolution_without_market(client):
    """Request markets"""

    resp = client.get('/markets/99999/AMZN/FQ1 2020/Revenue')

    assert resp.status_code == 404
    assert resp.json['message'] == 'This KPI Market does not exist'

def test_market_resolution_with_invalid_market_type(client):
    """Request markets"""

    resp = client.get('/markets/a/AMZN/FQ1 2020/Revenue')

    assert resp.status_code == 404

def test_market_resolution(client):
    """Request markets"""

    resp = client.get('/markets/1/AMZN/FQ1 2022/Revenue')
    
    print(resp.json)
    assert resp.status_code == 200
    assert resp.json['value'] == 1100000000

def test_unresolved_market(client):
    """Request markets"""

    resp = client.get('/markets/2/GOOG/FQ1 2022/Revenue')
    
    print(resp.json)
    assert resp.status_code == 202
    assert resp.json['value'] == False

def get_test_markets():
    '''Returns a set of markets to add'''

    market_list = []

    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, 'test_markets.csv')) as csv_fil:
        
        headers = [h.strip() for h in csv_fil.readlines(1)[0].split(',')]
        date_indices = [i for i, h in enumerate(headers) if h in ('expected_reporting_date')]
        for row in csv.reader(csv_fil, quotechar='"'):
            values = []
            for i, v in enumerate(row):
                if not v:
                    values.append(None)
                elif i in date_indices:
                    values.append(parser.parse(v.strip()).date())
                else:
                    values.append(eval(v.strip()))

            row_dict = dict(zip(headers,values))
            row_dict = {k:v for k, v in row_dict.items() if v is not None}

            market = Market(**row_dict)
            market_list.append(market)
    
    return market_list