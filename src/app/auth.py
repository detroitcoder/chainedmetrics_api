import os

from flask import Blueprint, jsonify, request, current_app
from datetime import timedelta
from flask_jwt_extended import create_access_token, current_user, jwt_required, decode_token
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidTokenError
from flask_jwt_extended import JWTManager

from .models import RequestAccess, User, db
from .utilities import (send_verification_email, send_resetpassword_email, 
                            subscribe_to_mailchimp_async)


jwt = JWTManager()
auth_bp = Blueprint('auth', __name__)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):

    email = jwt_data["sub"]
    return User.query.filter_by(email=email, active=True).one_or_none()

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
            identity=email,
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
        matic_recieved=current_user.matic_recieved,
        matic_recieved_date=current_user.matic_recieved_date
    )

@auth_bp.route('/user', methods=['POST'])
def add_user():
    '''
    Requests to add a user and if the payload is correct an email is sent to the user which requires them to verify
    the email address.

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
                        first_name:
                            type: string
                        last_name:
                            type: string
    responses:
        200:
            description: Success message
        400:
            description: Validation Error
        401:
            description: Not an Admin user
    '''

    email = request.json.get('email').lower().strip()
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    password = request.json.get('password')

    if not all((email, first_name, last_name, password)):
        return jsonify(message="All required arguments must be filled out"), 400
    elif User.query.filter_by(email=email).one_or_none():
        return jsonify(message="An account with this email already exists"), 400
    else:
        user = User(email=email, admin=False, active=False, first_name=first_name, last_name=last_name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        verify_token = create_access_token(identity=email, expires_delta=timedelta(days=1))
        send_verification_email(email, verify_token)
        subscribe_to_mailchimp_async(email)

        return jsonify(message=f'Email verification sent to {email}')

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
   