import os

from flask import Flask, json, jsonify
from flasgger import Swagger
from flask_migrate import Migrate

from .markets import markets_bp
from .auth import auth_bp
from .models import db
from .utilities import CustomJSONEncoder


app = Flask(__name__)
app.config.from_object('flask_config.{}'.format(
    os.environ.get('CHAINEDMETRICS_ENV', 'Development')
))
app.json_encoder = CustomJSONEncoder

swagger = Swagger(app)
db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)

app.register_blueprint(markets_bp, url_prefix='/markets')
app.register_blueprint(auth_bp, url_prefix='/auth')



