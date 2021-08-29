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