import os

class Config(object):
    DEBUG = True
    CHAINEDMETRICS_ENV = os.environ.get('CHAINEDMETRICS_ENV', 'Development')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Production(Config):
    DEVELOPMENT = False
    DEBUG = False
    DB_HOST = 'my.production.database'

class Development(Config):
    DEVELOPMENT = True
    DEBUG = True
    DB_HOST = 'chainedmetrics-dev-do-user-9754357-0.b.db.ondigitalocean.com'
    DB_USER = 'flask_app'
    DB_PORT = 25060
    DATABASE = 'metrics'
    DB_PASS = os.environ['DB_PASS']

    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DATABASE}'
