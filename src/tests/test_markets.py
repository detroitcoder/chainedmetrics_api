import os
import tempfile

import pytest

from app import create_app
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
    with app.app_context():
        command.upgrade(m.get_config(), 'head')

    with app.test_client() as client:
        yield client

def test_basic_request(client):
    """Request markets"""

    resp = client.get('/markets/')

    assert resp.json == dict(markets=[])