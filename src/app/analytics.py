import os
import requests
from collections import defaultdict
import datetime

class AMM(object):
    
    def __init__(self, high, low):
        
        self.high = high
        self.low = low
        self.long = 0
        self.short = 0
        self.transactions = []
        
    def process_transaction(self, transaction):
        '''
        Processes the transactions in the AMM
        '''
        
        delta_long, delta_short = transaction.transferAmount()
        if (delta_long, delta_short) == (0, 0):
            return None
        
        if transaction.isCompleteTransaction():
                transactionInfo = transaction.getTransactionInfo()
        else:
            print(transaction.all_transactions[0]['timeStamp'])
            transactionInfo = {
                'time': str(datetime.datetime.fromtimestamp(int(transaction.all_transactions[0]['timeStamp'])))
            }
            
        self.long += delta_long
        self.short += delta_short

        longPrice = self.short / (self.long + self.short)
        forecastedValue = float(self.low) + longPrice * float(self.high - self.low)
        
        transactionInfo['longPrice'] = longPrice
        transactionInfo['forecastedValue'] = forecastedValue
        transactionInfo['longBalance'] = self.long
        transactionInfo['shortBalance'] = self.short

        self.transactions.append(transactionInfo)    
    
    
class Transaction(object):
    '''
    This is an example of how to calculate the the
    '''
    
    def __init__(self, amm, collateral, long, short, _hash):
        
        self.collateral_transfer = None
        self.long_mint = None
        self.short_mint = None
        self.return_transfer = None
        
        self.amm_address = amm
        self.collateral_address = collateral
        self.long_address = long
        self.short_address = short
        self.all_transactions = []
        self.hash = _hash
        
        self.null_address = '0x0000000000000000000000000000000000000000'
        
    def isCompleteTransaction(self):
        '''
        Checks if the internal transactions occured within this transaction to be complete
        '''
        
        if all((self.collateral_transfer, self.long_mint, self.short_mint, self.return_transfer)):
            return True
        else:
            return False
    
    def isCollateralTransfer(self, txn):
        '''
        Checks if this is a collateral transfer transaction from a user to the amm
        '''
        
        if (self.collateral_address == txn['contractAddress'] and 
            self.amm_address == txn['to']):
            return True
        else:
            return False
        
    def isLongMint(self, txn):
        '''
        Check if this the minting of the long token
        '''
        
        if (self.null_address == txn['from'] and self.amm_address == txn['to'] 
            and txn['contractAddress'] == self.long_address):
            return True
        else:
            return False
        
    def isShortMint(self, txn):
        '''
        Check if this is the minting of the short token
        '''
        
        if (self.null_address == txn['from'] and self.amm_address == txn['to'] 
            and txn['contractAddress'] == self.short_address):
            return True
        else:
            return False
        
    def isReturnTransfer(self, txn):
        '''
        Checks if the user is returning the tokens
        '''

        if (self.amm_address == txn['from'] and txn['contractAddress'] in (self.long_address, self.short_address)):
            return True
        else:
            return False
    
    def classifyTransactionType(self, txn):
        '''
        Classifies the transaction type
        '''
            
        if self.isCollateralTransfer(txn):
            self.collateral_transfer = txn
        elif self.isLongMint(txn):
            self.long_mint = txn
        elif self.isShortMint(txn):
            self.short_mint = txn
        elif self.isReturnTransfer(txn):
            self.return_transfer = txn
        self.all_transactions.append(txn)

    def getTransactionInfo(self):
        '''
        Calcualtes information about the transaction based on info about the transaction
        '''

        assert self.isCompleteTransaction(), 'Incomplete transaction'

        time = str(datetime.datetime.fromtimestamp(int(self.collateral_transfer['timeStamp'])))
        investmentAmount = int(self.collateral_transfer['value'])
        orderType = 'long' if self.return_transfer['contractAddress'] == self.long_address else 'short'
        
        try:
            pricePerToken = float(investmentAmount) / int(self.return_transfer['value'])
        except ZeroDivisionError:
            pricePerToken = 0
        
        return {
            'account': self.collateral_transfer['from'],
            'time': time,
            'investmentAmount': investmentAmount,
            'orderType': orderType,
            'pricePerToken': pricePerToken,
            'transactionType': 'buy',
            'returnAmount': int(self.return_transfer['value']),
            'isComplete': 'True'
        }

    def transferAmount(self):
        '''
        Calculates the long and short tokens that at transfered in and out of the AMM for the short and long tokens
        '''
        
        long, short = 0, 0
        for txn in self.all_transactions:
            if txn.get('from') == self.amm_address:
                if txn.get('contractAddress') == self.long_address:
                    long -= int(txn['value'])
                elif txn.get('contractAddress') == self.short_address:
                    short -= int(txn['value'])

            elif txn.get('to') == self.amm_address:
                if txn.get('contractAddress') == self.long_address:
                    long += int(txn['value'])
                elif txn.get('contractAddress') == self.short_address:
                    short += int(txn['value'])

        return long, short

def calc_pnl(transactions, long_price=None, short_price=None):
    '''
    Calculates the PnL from the transactions for a market for each address

    Arguments:
        transactions (list): Output from get_historical_transactions for a market
        long_price (float): Price of the long token
        short_price (float): Price of the short token

    Returns:
        dict: Dictionary of PnL for each address
    
    Notes:
        If long_price and short_price are not provided, the prices from the last transaction are used
    '''

    pnl = defaultdict(lambda: 0)
    balances = {'long': defaultdict(lambda: 0), 'short': defaultdict(lambda: 0)}

    if long_price is None:
        long_price, short_price = transactions[-1]['longPrice'], 1 - transactions[-1]['longPrice']
        
    for txn in transactions:
        account = txn['account']
        if txn.get('isComplete') == 'True':
            if txn['transactionType'] == 'buy':
                if txn['orderType'] == 'long':
                    pnl[account] -= txn['investmentAmount']
                    balances['long'][account] += txn['returnAmount']
                elif txn['orderType'] == 'short':
                    pnl[account] -= txn['investmentAmount']
                    balances['short'][account] += txn['returnAmount']
            elif txn['transactionType'] == 'sell':
                if txn['orderType'] == 'long':
                    pnl[account] += txn['returnAmount']
                    balances['long'][account] -= txn['investmentAmount']
                elif txn['orderType'] == 'short':
                    pnl[account] += txn['returnAmount']
                    balances['long'][account] += txn['investmentAmount']
            
    for (acc, bal) in balances['long'].items():
        pnl[acc] += bal * long_price
        
    for (acc, bal) in balances['short'].items():
        pnl[acc] += bal * short_price

    return pnl

def get_historical_transactions(amm_address, high, low, collateral, long, short, api_token, date=None):

    amm = AMM(high, low)
    transaction_dict = call_polyscan_api(amm_address, api_token)
    transaction = Transaction(amm_address, collateral, long, short, transaction_dict['result'][0]['hash'])
    for txn in transaction_dict['result']:
        # Filter out transacitons before date
        if date is not None and int(txn['timeStamp']) < date:
            continue

        if txn['hash'] != transaction.hash:
            amm.process_transaction(transaction)
            transaction = Transaction(amm_address, collateral, long, short, txn['hash'])
            
        transaction.classifyTransactionType(txn)
    
    amm.process_transaction(transaction)
    
    return amm.transactions


def call_polyscan_api(token_address, api_token):
    '''
    Queries polyscan for the historical transactions of the AMM
    '''

    print(f'Getting Issuances for {token_address}')
    url = (
        "https://api.polygonscan.com/api?module=account&action=tokentx&"
        f"address={token_address}&sort=asc&"
        f"apikey={api_token}"
    )

    print(url)
    resp = requests.get(url).json()
    return resp