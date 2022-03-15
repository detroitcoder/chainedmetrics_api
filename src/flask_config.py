import os

class Config(object):
    DEBUG = True
    CHAINEDMETRICS_ENV = os.environ.get('CHAINEDMETRICS_ENV', 'Development')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAILCHIMP_URL = 'https://us5.api.mailchimp.com/3.0'
    MAILCHIMP_LIST = '10165fe090'
    MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'serviceaccount@chainedmetrics.com'
    MAIL_PASSWORD = os.environ['GMAIL_PASS']
    POLYGONSCAN_TOKEN = os.environ['POLYGONSCAN_TOKEN']


class Production(Config):
    DEVELOPMENT = False
    DEBUG = False
    DB_HOST = 'chainedmetrics-prod-do-user-9754357-0.b.db.ondigitalocean.com'
    DB_USER = 'flask_app'
    DB_PORT = 25060
    DATABASE = 'metrics'
    DB_PASS = os.environ['DB_PASS']
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    JWT_TOKEN_LOCATION = "headers"
    URL = 'https://chainedmetrics.com'

    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DATABASE}'

class Development(Config):
    DEVELOPMENT = True
    DEBUG = True
    DB_HOST = 'chainedmetrics-dev-do-user-9754357-0.b.db.ondigitalocean.com'
    DB_USER = 'flask_app'
    DB_PORT = 25060
    DATABASE = 'metrics'
    DB_PASS = os.environ['DB_PASS']
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    JWT_TOKEN_LOCATION = "headers"
    URL = 'https://dev.chainedmetrics.com'

    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DATABASE}'
