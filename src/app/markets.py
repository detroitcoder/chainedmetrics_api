from flask import Blueprint, jsonify, current_app, request
from cachetools import cached, TTLCache
from .models import Market
from .analytics import get_historical_transactions, calc_pnl
from collections import defaultdict
from dateutil.parser import parse
from random import randint
from datetime import datetime, timedelta


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


@markets_bp.route('/historical_prices/<int:market>')
def historical_prices(market):
    '''
    Endpoint for returning KPI values
    ---
    parameters:
      - name: market
        in: path
        type: integer
        required: true
    responses:
        200:
            description: An array of historical prices and transactions
        202:
            description: The market does exist but the Value has not been set yet
        400:
            description: The request arguments in the URL were invalid
        404:
            description: The requested market does not exist
    '''

    if not market:
        return jsonify(message='All paramaters must be specified'), 400
    
    market = Market.query.filter_by(id=market).one_or_none()
    if market is None:
        return jsonify(message='This KPI Market does not exist'), 404
    else:
        historical_data =  get_fake_historical_transactions(
            market.high,
            market.low,
            market.beat_price
        )
        return jsonify(message='Success', value=historical_data)
        # Comment out historical trasnsaction to better simulate data
        # historical_data = get_historical_transactions(
        #     market.broker_address.strip().lower(), 
        #     market.high,
        #     market.low,
        #     '0x79ec35384829ba7a75759a057693ce103b077bb1', #collateral_token
        #     market.beat_address.strip().lower(),
        #     market.miss_address.strip().lower(),
        #     current_app.config['POLYGONSCAN_TOKEN'])

        # return jsonify(message='Success', value=historical_data)

@markets_bp.route('/pnl')
def pnl():
    '''
    Endpoint for querrying PNL values based on different filters such as ticker, date and market
    ---
    parameters:
      - name: ticker
        in: query
        type: string
        required: false
      - name: date
        in: query
        type: string
        required: false
      - name: marketId
        in: query
        type: integer
        required: false
    responses:
        200:
            description: A sorted array of PNL based on the filter with the address and PnL
        400:
            description: The request arguments in the URL were invalid
        404:
            description: The requested market does not exist
    '''

    ticker = request.args.get('ticker')
    date = request.args.get('date')
    marketId = request.args.get('marketId')

    print(ticker, date, marketId)

    if date:
        try:
            date = parse(date).timestamp()
        except ValueError:
            return jsonify(message='Invalid date format'), 400

    markets = Market.query.filter(Market.low > 0)
    if ticker:
        markets = markets.filter(Market.ticker==ticker)
    if marketId:
        markets = markets.filter(Market.id==marketId)

    pnl = defaultdict(lambda: 0)
    for market in markets:
        historical_data = get_historical_transactions(
            market.broker_address.strip().lower(), 
            market.high,
            market.low,
            '0x79ec35384829ba7a75759a057693ce103b077bb1', #collateral_token
            market.beat_address.strip().lower(),
            market.miss_address.strip().lower(),
            current_app.config['POLYGONSCAN_TOKEN'],
            date)

        print(historical_data)
        
        transaction_pnl = calc_pnl(historical_data)
        for address, pnl_value in transaction_pnl.items():
            pnl[address] += pnl_value
        
    results = sorted(pnl.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify(message='Success', value=results)

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
    for m in markets:
        m['chartData'] = get_historical_data_for_spark()

    return markets

def get_historical_data_for_spark():
    '''
    Retuns random data for the spark charts on the web page
    '''

    lst = [50]
    for i in range(100):
        if randint(0, 4) == 0:
            lst.append(lst[-1] + randint(-35, 30))
        else:
            lst.append(lst[-1] + randint(-6, 10))
    return lst
        
def get_fake_historical_transactions(high, low, beat_price):
    '''
    Generates fake historical transaction data for more realistic simulations
    
    '''
    high = float(high)
    low = float(low)
    start = datetime.now() - timedelta(hours=randint(1, 3))
    transactions = [{
        'time': start.strftime('%Y-%m-%d %T'),
        'forecastedValue': low + (high-low) / 2,
        'investmentAmount': randint(1000, 50000)
    }]
    
    for i in range(50):

        up = randint(0, 9) <= 3
        for i in range(7):
            next_trans = transactions[-1]
            next_time = parse(next_trans['time'])
            next_value = float(next_trans['forecastedValue'])
            
            if randint(0, 6) == 0:
                last_time = next_time - timedelta(hours=randint(2,48), minutes=randint(1, 15))
            else:
                last_time = next_time - timedelta(minutes=randint(10,120))

            percent = (randint(1, 15) / 100)
            if up:
                last_value = (high - next_value) * percent + next_value
            else:
                last_value = next_value - (next_value - low) * percent

            investment_amount = int(50000 * percent)

            transactions.append({
                'time': last_time.strftime('%Y-%m-%d %T'),
                'forecastedValue': last_value,
                'investmentAmount': investment_amount
            })
            print(percent, up, last_time, last_value, investment_amount)

    transactions.reverse()
    return transactions
        
        


        

    
     

