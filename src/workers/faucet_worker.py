import asyncio
import psycopg2
import traceback
import brownie
import os
import json

DEV_ADDRESS = '0x3BEBd505f2418ba2Fac94110F4E1D76b01B262a7'
PROD_ADDRESS = '0x35FE7a74668EC648038E615659710f140e591B82'
DEV_PAYOUT = 0.00025
PROD_PAYOUT = 0.2
ACCOUNT = brownie.accounts.add(os.environ['PRIVATE_KEY'])

def clear_queue(connection):
    '''
    Iterates through the queue until nothing is left and then
    it returns
    '''

    while True:
        cursor = connection.cursor()
        cursor.execute('BEGIN')
        try:
            id, email, address = select_and_lock_row(cursor)
        except Exception as e:
            cursor.execute('ROLLBACK TRANSACTION;')
            raise

        if not id:
            cursor.execute('ROLLBACK TRANSACTION;')
            return
        try:
            success, msg, transfer_quantity = process_row(id, email, address)
        except Exception as e:
            success = False
            msg = traceback.format_exc()
            print(msg)
        
        if success:
            update_user_and_delete_row(cursor, id, email, transfer_quantity)
        else:
            update_row_with_error(cursor, id, msg)


def get_matic_contract_and_send(email, address):
    
    faucet = get_faucet()
    faucet.requestMatic(email.lower(), address, {'from': ACCOUNT})

    payout = PROD_PAYOUT if os.getenv('CHAINEDMETRICS_ENV') == 'Production' else DEV_PAYOUT
    return (True, '', payout)

def get_faucet():

    if os.getenv('CHAINEDMETRICS_ENV') == 'Production':
        matic_address = PROD_ADDRESS
    else:
        matic_address = DEV_ADDRESS

    with open('matic_faucet_abi.json') as fil:
        faucet_abi = json.load(fil)

    faucet = brownie.Contract.from_abi('MaticFaucet', matic_address, faucet_abi)

    return faucet

def select_and_lock_row(cursor):
    '''
    Selects and locks a row to process in the queue and returns
    the corresponding email and address

    Arguments:
        None

    Returns:
        email (str): The email that is being processed
        address (str): The address that is being processed
    '''

    cursor.execute('''
        SELECT id, email, address FROM public.matic_faucet_queue
        WHERE error_msg is null
        ORDER BY id
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    ''')

    result = cursor.fetchone()

    if result:
        return result
    else:
        return (None, None, None)

def process_row(id, email, address):

    success, msg, amount_transfered = get_matic_contract_and_send(email, address)

    return (success, msg, amount_transfered)


def update_user_and_delete_row(cursor, id, email, quantity):
    '''
    Updates the users table to indicate the user recieved matic and
    deletes the row after it has been processed from the queue. Once 
    this is done it commits the transaction.

    Arguments:
        cursor (sqlalchemy.conection.cursor): The currsor for the current connection
        id (int): The id for the reccord to delete in queue table
        email (str): The email in the user table
        quantity (float): The quantity of matic sent

    Returns:
        None
    '''

    cursor.execute(f'''
    UPDATE public.user
    SET matic_recieved = %s, matic_recieved_date = NOW()
    WHERE email = %s;

    DELETE FROM public.matic_faucet_queue
    WHERE id = %s;
    COMMIT;
    ''', (quantity, email, id)
    )

def update_row_with_error(cursor, id, msg):
    '''
    Updates a record if there is an error

    Arguments:
        cursor (sqlalchemy.conection.cursor): The currsor for the current connection
        id (int): The id for the reccord to delete
        msg (string): The error string to store in the table

    Returns:
        None
    '''

    cursor.execute('''
        UPDATE public.matic_faucet_queue
        SET error_msg = %s, error_time = NOW()
        WHERE id = %s;
        COMMIT;
    ''', (msg, id)
    )

def handle_notify():
    print('handle notify')

    try:
        conn.poll()
    except psycopg2.OperationalError as e:
        print('Saw error, clearing queue, and exiting')
        clear_queue(conn)
        return

    for notify in conn.notifies:
        print('n')
        clear_queue(conn)

    conn.notifies.clear()   
    print('ended')

if __name__ == "__main__":

# dbname should be the same for the notifying process
    conn = psycopg2.connect(
        host="chainedmetrics-dev-do-user-9754357-0.b.db.ondigitalocean.com", 
        port=25060,
        dbname="metrics", 
        user="flask_app", 
        password="foga2xjyyivvow5c"
    )

    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    print('Loading project and connecting to network')
    brownie.project.load('.', 'MaticFaucetProject')
    brownie.network.connect('polygon-main')
    print('Clearing queue')
    clear_queue(conn)

    print('Queue cleared')

    cursor = conn.cursor()
    cursor.execute(f"LISTEN faucet_request;")

    print('Starting server')
    loop = asyncio.get_event_loop()
    loop.add_reader(conn, handle_notify)
    try:
        loop.run_forever()
    except Exception:
        print('Closing Connection')
        conn.close()