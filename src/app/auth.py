import os
import time

from flask import Blueprint, jsonify, request, current_app
from datetime import timedelta
from flask_jwt_extended import create_access_token, current_user, jwt_required, decode_token
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidTokenError
from flask_jwt_extended import JWTManager

from web3.auto import w3
from eth_account.messages import defunct_hash_message
from eth_keys.exceptions import BadSignature, ValidationError

from .models import RequestAccess, User, db
from .utilities import (send_verification_email, send_resetpassword_email, 
                            subscribe_to_mailchimp_async)


jwt = JWTManager()
auth_bp = Blueprint('auth', __name__)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):

    address = jwt_data["sub"]
    
    return User.query.filter_by(address=address).one_or_none()

@jwt.expired_token_loader
def exipred_token_callback(jwt_header, jwt_payload):

    return jsonify(message='Token has expired. Refresh using the /auth/login endpoint'), 401

@auth_bp.route('/login', methods=['POST'])
def login():
    '''
    Logs a user into chainedmetrics and retuns a JWT token valid for 7 days

    Endpoint for Logging into chained metrics that requires a username and \
    password and returns a JWT token. This token is then required to be in \
    the header of all restricted endpoints.

    ---
    requestBody:
        required: true
        description: The user's email and passsword for chained metrics
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        email:
                            type: string
                        password:
                            type: string
    responses:
        200:
            description: Successful response with the JWT as access_token
        401:
            description: Incorrect user name or password
    '''

    email = request.json.get('email')
    password = request.json.get('password')

    user = User.query.filter_by(email=email.lower()).one_or_none()

    if not user or not user.check_password(password):
        return jsonify(dict(message='Wrong username or password')), 401
    else:
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )

        return jsonify(dict(message='Success', access_token=access_token))

@auth_bp.route('/login2', methods=['POST'])
def login2():
    '''
    Logs a user into chainedmetrics with web3 signature and retuns a JWT token valid for 7 days

    Endpoint for Logging into chained metrics using a web3 signature and their \
    address. A JWT token is returned and is then required to be in \
    the header of all restricted endpoints.

    ---
    requestBody:
        required: true
        description: The user's email and passsword for chained metrics
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        address:
                            type: string
                        signature:
                            type: string
                        message:
                            type: string
    responses:
        200:
            description: Successful response with the JWT as access_token
        401:
            description: Incorrect address or signature
    '''

    address = request.json.get('address')
    signature = request.json.get('signature')
    user_message = request.json.get('message')

    if not address or not signature:
        return jsonify(dict(message='No signature provided')), 401

    # Construct the expected message hash from the address and signature
    now = time.time()
    rounded_now = now - (now % 600)
    domain = request.headers.get('Host')
    message = 'Signing in to {} at {:.0f}'.format(domain, rounded_now)
    message_hash = defunct_hash_message(text=message)
    print('expected_message:', message)
    print('user_message:', user_message)
    print('messages equal:', message == user_message)
    print('user_address:', address)
    # Verify the signature matches the address and message hash
    try:
        signer = w3.eth.account.recoverHash(message_hash, signature=signature)
    except (BadSignature, ValidationError):
        return jsonify(dict(message='Invalid signature')), 401

    print('signer_address:', signer)
    if signer != address:
        return jsonify(dict(message='Wrong signature')), 401
    else:
        user = User.query.filter_by(address=address).one_or_none()

        if not user:
            user = User(address=address, active=True)
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(
            identity=user.address,
            expires_delta=timedelta(days=7)
        )

        return jsonify(dict(message='Success', access_token=access_token))

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def user():
    '''
    Information about the User
    Returns user information including username, email, first name, last name, if they are an admin, is the account active, and when the account was created

    It does require an valid token to be in the header in order to see this information
    ---
    security:
        - bearerAuth: []
    responses:
        200:
            description: JSON object for relevant user information
    '''

    return jsonify(
        email=current_user.email,
        admin=current_user.admin,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        active=current_user.active,
        created_on=current_user.created_on,
        address=current_user.address,
        matic_recieved=current_user.matic_recieved,
        matic_recieved_date=current_user.matic_recieved_date,
        notifications_portfolio_events=current_user.notifications_portfolio_events,
        notifications_market_events=current_user.notifications_market_events
    )

@auth_bp.route('/user', methods=['POST'])
def add_user():
    '''
    Add new user
    Requests to add a user and if the payload is correct an email is sent to the user which requires them to verify the email address.

    Used to initially create the account
    ---
    requestBody:
        required: true
        description: Required fields for the user
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        email:
                            type: string
                        password:
                            type: string
                        username:
                            type: string
                        address:
                            type: string
                        notifications_portfolio_events:
                            type: boolean
                        notifications_market_events:
                            type: boolean

    responses:
        200:
            description: Success message
        400:
            description: Validation Error
        401:
            description: Not an Admin user
    '''

    email = request.json.get('email').lower().strip()
    password = request.json.get('password')
    username = request.json.get('username', '')
    address = request.json.get('address', '').strip()
    notifications_market_events = request.json.get('notifications_market_events', False)
    notifications_portfolio_events = request.json.get('notifications_portfolio_events', False)

    if not all((email, password)):
        return jsonify(message="All required arguments must be filled out"), 400
    elif not all((isinstance(notifications_market_events, bool), isinstance(notifications_portfolio_events, bool))):
        return jsonify(message="Notification flags muss be boolean")
    elif User.query.filter_by(email=email).one_or_none():
        return jsonify(message="An account with this email already exists"), 400
    else:
        user = User(
            email=email, admin=False, active=False, username=username, 
            address=address,
            notifications_market_events = notifications_market_events,
            notifications_portfolio_events=notifications_portfolio_events, 
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        verify_token = create_access_token(identity=email, expires_delta=timedelta(days=1))
        send_verification_email(email, verify_token)
        subscribe_to_mailchimp_async(email)

        return jsonify(message=f'Email verification sent to {email}')

@auth_bp.route('/user', methods=['PUT'])
@jwt_required()
def update_user():
    '''
    Update User Settings
    Requests to update a user's settings

    Used to initially create the account
    ---
    requestBody:
        required: true
        description: Required fields for the user
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        email:
                            type: string
                        password:
                            type: string
                        username:
                            type: string
                        address:
                            type: string
                        notifications_portfolio_events:
                            type: boolean
                        notifications_market_events:
                            type: boolean

    responses:
        200:
            description: Success message
        400:
            description: Validation Error
        401:
            description: Not an Admin user
    '''

    email = request.json.get('email')
    username = request.json.get('username')
    address = request.json.get('address')
    notifications_market_events = request.json.get('notifications_market_events')
    notifications_portfolio_events = request.json.get('notifications_portfolio_events')

    if email:
        email = email.lower().strip()
        if User.query.filter_by(email=email).one_or_none() and current_user.email != email:
            return jsonify(message='Email is already in use'), 400
        current_user.email = email
    
    if username:
        username = username.strip().lower()
        if User.query.filter_by(username=username).one_or_none() and current_user.username != username:
            return jsonify(message='Username is already in use'), 400
        current_user.username = username
    
    if address:
        address = address.strip()
        if User.query.filter_by(address=address).one_or_none() and current_user.address != address:
            return jsonify(message='Address is already in use'), 400
        current_user.address = address

    if isinstance(notifications_market_events, bool):
        current_user.notifications_market_events = notifications_market_events
    
    if isinstance(notifications_portfolio_events, bool):
        current_user.notifications_portfolio_events = notifications_portfolio_events
    
    db.session.commit()

    return jsonify(message='Updated user settings')


@auth_bp.route('/verifyuser', methods=['POST'])
def verify_user():
    '''
    Used to verify a user after they authenticate validate their email address. They were given a token that lasts for 24 hours
    and if this token is returned to this API it will return a 200 and a valid JWT token just like the one returned
    from the login endpoint

    Verifies the user's email is accurate and activates the user
    ---
    requestBody:
        required: true
        description: The token body
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        verifytoken:
                            type: string
    responses:
        200:
            description: Success message with the JWT token
        400:
            description: Verify token is not found in the payload
        404:
            description: There is not a user registered for this email yet. Possibly malicious
        410:
            description: The user already verified this account but is valid
        403:
            description: The token is expired or invalid. See message
    '''

    verifytoken = request.json.get('verifytoken')
    if not verifytoken:
        return jsonify(message="verifytoken is missing"), 400

    try:
        email = decode_token(verifytoken)['sub']

        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(days=7)
        )

        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            return jsonify('No registered user for this email'), 404
        elif user.active:
            return jsonify('User has has already activated account'), 410
        else:

            user.active = True
            db.session.commit()

            return jsonify(dict(message='Success', access_token=access_token))
    
    except ExpiredSignatureError:
        return jsonify(message='Expired verifytoken'), 403
    except (DecodeError, InvalidTokenError):
        return jsonify(message='Invalied verifytoken'), 403  

@auth_bp.route('/forgotpassword', methods=['POST'])
def forgot_password():
    '''
    Requests an email to be sent to request a password reset

    Sends an email to reset the password to the email if it exists
    ---
    requestBody:
        required: true
        description: The token body
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        email:
                            type: string
    responses:
        200:
            description: Success confirmation that the email is
        400:
            description: Verify token is not found in the payload
    '''

    email = request.json.get('email').lower().strip()
    if not email:
        return jsonify(message="Email is missing"), 400

    user = User.query.filter_by(email=email).one_or_none()
    if not user:
        print('No User found')
        pass
    else:
        ('email sent')
        reset_token = create_access_token(identity=email, expires_delta=timedelta(hours=1))
        send_resetpassword_email(email, reset_token)
        
    return jsonify(message="If the email exists, a reset password link has been sent")


@auth_bp.route('/resetpassword', methods=['POST'])
def reset_password():
    '''
    Endpoint to reset the password. It requires both the token and the new password and runs validation on both. If successful it returns the valid JWT token

    Checks if the reset password is valid and if so resets the password to the new password
    ---
    requestBody:
        required: true
        description: The token body
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        resettoken:
                            type: string
                        password:
                            type: string
    responses:
        200:
            description: Success message with the JWT token
        400:
            description: Verify token is not found in the payload
        404:
            description: There is not a user registered for this email yet. Possibly malicious
        410:
            description: The user already verified this account but is valid
        403:
            description: The token is expired or invalid. See message
    '''

    resettoken = request.json.get('resettoken')
    password = request.json.get('password')

    if not resettoken:
        return jsonify(message="resettoken is missing"), 400
    elif not password:
        return jsonify(message="missing password")

    try:
        email = decode_token(resettoken)['sub']

        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            return jsonify('No registered user for this email'), 404
        else:
            user.set_password(password)
            db.session.commit()

            access_token = create_access_token(
                identity=email,
                expires_delta=timedelta(days=7)
            )

            return jsonify(message='Success', token=access_token)
    
    except ExpiredSignatureError:
        return jsonify(message='Expired verifytoken'), 403
    except (DecodeError, InvalidTokenError):
        return jsonify(message='Invalied verifytoken'), 403 


@auth_bp.route('/subscribe', methods=['POST'])
def subscribe():
    '''
    Endpoint for subscribing to the newsletter using MailChimp

    Subscribes to MailChimp NewsLetter from Chained Metrics team
    ---
    requestBody:
        description: Information about the user that is requesting access
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        email:
                            required: true
                            type: string

    responses:
        200:
            description: Success Response
        400:
            description: Validation error on arguments. See Response
    '''

    email = request.json.get('email')
    
    if not email:
        return jsonify(dict(message="Email is missing"))
    else:
        subscription_result = subscribe_to_mailchimp(email)

        if subscription_result is True:
            return jsonify(dict(message="Success")), 200
        else:
            return jsonify(dict(message=subscription_result)), 400
   