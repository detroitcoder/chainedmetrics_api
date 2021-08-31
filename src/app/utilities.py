import decimal
import json

from datetime import date, datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):

        if isinstance(obj, date) or isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)

SWAGGER_TEMPLATE = {
    "swagger": "3.4.0",
    "info": {
        "title": "Chained Metrics API",
        "description": ("This is the backend API for all REST API calls. "
                        "For all requests that require authentication, "
                        "a JWT token needs to be added to the header. See the /auth/login endpoint for details"),
        "contact": {
        "responsibleOrganization": "ChainedMetrics",
        "responsibleDeveloper": "Michael Watson",
        "email": "michael@chainedmetrics.com"
        },
        "termsOfService": "https://chainedmetrics.com/termsofservice",
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {           # arbitrary name for the security scheme
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
}