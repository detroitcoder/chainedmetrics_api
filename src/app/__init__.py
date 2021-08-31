import os

from flask import Flask, json, jsonify
from flasgger import Swagger
from flask_migrate import Migrate
from flask_jwt_extended.exceptions import NoAuthorizationError

from .markets import markets_bp
from .auth import auth_bp, jwt
from .models import db
from .utilities import CustomJSONEncoder, SWAGGER_TEMPLATE


app = Flask(__name__)
app.config.from_object('flask_config.{}'.format(
    os.environ.get('CHAINEDMETRICS_ENV', 'Development')
))
app.json_encoder = CustomJSONEncoder

app.config['SWAGGER'] = dict(openapi='3.0.2')
swagger = Swagger(app, template=SWAGGER_TEMPLATE)

db.init_app(app)
jwt.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)


app.register_blueprint(markets_bp, url_prefix='/markets')
app.register_blueprint(auth_bp, url_prefix='/auth')


@app.errorhandler(500)
def handle_500(err):
    
    if isinstance(err.original_exception, NoAuthorizationError):
        return jsonify(dict(
            message=(
                'Invalid or Unset JWT token. Ensure your session '
                'has a valid token by logging in and the access_token_cookie is set.'
                )
        )), 401

    else:
        try:
            err.with_traceback()
        except Exception:
            app.logger.exception('500 Unhandled Error')
            return jsonify(dict(message='There was an unhandled server excption. See server logs for details')), 500
