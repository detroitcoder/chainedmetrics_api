from flask import Blueprint, jsonify
from cachetools import cached, TTLCache
from .models import Market


markets_bp = Blueprint('markets', __name__)

@markets_bp.route('/', methods=['GET'])
def metrics():
    '''
    Endpoint listing all markets for company KPIs
    This is an unauthenticated to get all available KPIs
    ---
    responses:
        200:
            description: A list of all markets available
    '''

    markets = get_markets()

    return jsonify(dict(markets=markets))

# set ttl = 5 minutes (300 seconds)
@cached(cache=TTLCache(maxsize=10, ttl=300))
def get_markets():
    '''
    Returns the list available KPI Markets

    Ags:
        None
    
    Retrns:
        markets (list): A list of dictionaries. Each dict has key value pairs for the row in the table

        eg. markets = [
                dict(
                    ticker='NFLX',
                    metric='Net New Subscribers',
                    fiscal_period='FQ1 2022',
                    value='2.21M',
                    market_id=123,
                    tokens_issued=10,
                    beat_price=0.5,
                    closed=False
                ),
                ...
            ]
    '''

    markets = Market.query.all()
    markets = [{k: v for k, v in row.__dict__.items() if not k.startswith('_')} for row in markets]

    return markets
