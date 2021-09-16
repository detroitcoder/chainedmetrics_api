import requests
import os

from flask import Blueprint, jsonify, request, current_app
from datetime import timedelta
from flask_jwt_extended import create_access_token, current_user, jwt_required
from flask_jwt_extended import JWTManager

from .models import RequestAccess, User, db


jwt = JWTManager()
auth_bp = Blueprint('auth', __name__)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):

    email = jwt_data["sub"]
    return User.query.filter_by(email=email).one_or_none()

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

    user = User.query.filter_by(email=email).one_or_none()

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
        created_on=current_user.created_on
    )

@auth_bp.route('/user', methods=['POST'])
@jwt_required()
def add_user():
    '''
    REQUIRES ADMIN PRIVLEGES FOR TESTING ONLY: Endpoint to create a new user

    Enables programatic access to create new users. Must be authenticated with a user with admin privleges
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
                        admin:
                            type: boolean
    security:
        - bearerAuth: []
    responses:
        200:
            description: Success message
        400:
            description: Validation Error
        401:
            description: Not an Admin user
    '''

    if not current_user.admin:
        return jsonify(message="User does not have admin privleges to create users"), 401

    else:
        email = request.json.get('email')
        admin = request.json.get('admin')
        first_name = request.json.get('first_name')
        last_name = request.json.get('last_name')
        password = request.json.get('password')

        if not all((email, first_name, last_name, password)):
            return jsonify(message="All required arguments must be filled out"), 400
        elif admin not in (True, False):
            return jsonify(message="All required arguments must be filled out"), 400

        user = User(email=email, admin=admin, active=True, first_name=first_name, last_name=last_name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify(message='Success')

@auth_bp.route('/requestaccess', methods=['POST'])
def request_access():
    '''
    Endpoint for requesting access to the Exchange UI

    This endpoint is used to request access to chainedmetrics.com
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
                        full_name:
                            required: true
                            type: string
                        reason:
                            type: string
                        company:
                            type: string
    responses:
        200:
            description: Success Response
        400:
            description: Validation error on arguments. See Response
    '''

    full_name = request.json.get('full_name')
    email = request.json.get('email')
    reason = request.json.get('reason')
    company = request.json.get('company')
    
    if email and full_name:

        email_subscription = subscribe_to_mailchimp(email)
        if email_subscription is True:
            request_access = RequestAccess(full_name=full_name, email=email, reason=reason, company=company)
            db.session.add(request_access)
            db.session.commit()
            
            return jsonify(dict(message='Success'))
        else:
            return jsonify(dict(message=email_subscription)), 400
    
    else:

        return jsonify(dict(message='Email and Full Name must be filled out.')), 400


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
   

def subscribe_to_mailchimp(email):
    '''
    Adds a user's email to the Mail Chimp News letter

    Args:
        email (str): The email to Add
    
    Returns:
        result (True or Error msg): True if successful or a string of an error message
    '''

    mailchimp_url = '{url}/lists/{list}/members'.format(
        url=current_app.config['MAILCHIMP_URL'],
        list=current_app.config['MAILCHIMP_LIST']
    )

    r = requests.post(
        mailchimp_url,
        auth=('key', current_app.config['MAILCHIMP_API_KEY']),
        json=dict(
            email_address=email,
            status='subscribed'
        ),
        timeout=1
    )

    if r.status_code < 300:
        return True
    else:
        data = r.json()
        if 'detail' in data:
            return data['detail']
        else:
            return 'Unable to subscribe at this time, please try again later'
