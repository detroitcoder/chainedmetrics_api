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

@markets_bp.route('/<int:market>/<string:ticker>/<string:fiscal_period>/<string:metric>')
def get_metric_value(market, ticker, fiscal_period, metric):
    '''
    Endpoint for returning KPI values
    ---
    parameters:
      - name: market
        in: path
        type: integer
        required: true
      - name: ticker
        in: path
        type: string
        required: true
      - name: fiscal_period
        in: path
        type: string
        required: true
      - name: metric
        in: path
        type: string
        required: true
    responses:
        200:
            description: The value of the KPI
        202:
            description: The market does exist but the Value has not been set yet
        400:
            description: The request arguments in the URL were invalid
        404:
            description: The requested market does not exist
    '''

    if not all([market, ticker, fiscal_period, metric]):
        return jsonify(message='All paramaters must be specified'), 400
    
    value = lookup_result(market, ticker, fiscal_period, metric)
    if value is None:
        return jsonify(message='This KPI Market does not exist'), 404
    elif value is False:
        return jsonify(messsage='This KPI Market has not resolved', value=False), 202
    else:
        return jsonify(message='Success', value=value)


# set ttl = 5 minutes (300 seconds)
@cached(cache=TTLCache(maxsize=10, ttl=300))
def lookup_result(market, ticker, fiscal_period, metric):
    '''
    Returns the value for the metric

    Ags:
        None
    
    Retrns:
        metric_value (float): A singleton float if the KPI is resolved or None
    '''

    market = Market.query.filter_by(id=market, ticker=ticker, fiscal_period=fiscal_period, metric=metric).one_or_none()
    if market is None:
        return None
    if market.resolved_value is None:
        return False
    else:
        return market.resolved_value

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
    markets = Market.query.filter(Market.beat_address.isnot(None)).all()
    markets = [{k: v for k, v in row.__dict__.items() if not k.startswith('_')} for row in markets]

    return markets
