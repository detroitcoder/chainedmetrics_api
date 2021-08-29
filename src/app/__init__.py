import os


from flask import Flask, json, jsonify
from flasgger import Swagger
from flask_migrate import Migrate

from .markets import markets_bp
from .models import db
from .utilities import CustomJSONEncoder

app = Flask(__name__)
app.config.from_object('flask_config.{}'.format(
    os.environ.get('CHAINEDMETRICS_ENV', 'Development')
))

swagger = Swagger(app)
db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)


app.register_blueprint(markets_bp, url_prefix='/markets')

class DecimalEncoder(json.JSONEncoder):
    
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])


        return super(DecimalEncoder, self).default(o)

app.json_encoder = CustomJSONEncoder
