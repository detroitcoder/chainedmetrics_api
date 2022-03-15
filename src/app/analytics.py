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

        buyer = self.collateral_transfer['from']
        time = str(datetime.datetime.fromtimestamp(int(self.collateral_transfer['timeStamp'])))
        quantity = self.collateral_transfer['value']
        orderType = 'long' if self.return_transfer['contractAddress'] == self.long_address else 'short'
        
        try:
            pricePerToken = float(self.collateral_transfer['value']) / int(self.return_transfer['value'])
        except ZeroDivisionError:
            pricePerToken = 0
        
        return {
            'buyer': buyer,
            'time': time,
            'quantity': quantity,
            'orderType': orderType,
            'pricePerToken': pricePerToken,
            'transactionType': 'buy'
        }

    def transferAmount(self):
        '''
        Calculates the long and short tokens that at transfered in and out of the AMM for the short and long tokens
        '''
        
        long, short = 0, 0
        for txn in self.all_transactions:
            print(self.amm_address)
            print(txn['from'])
            print(txn['to'])
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

def get_historical_prices(amm_address, high, low, collateral, long, short, api_token):

    amm = AMM(high, low)
    transaction_dict = call_polyscan_api(amm_address, api_token)
    transaction = Transaction(amm_address, collateral, long, short, transaction_dict['result'][0]['hash'])
    for txn in transaction_dict['result']:
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