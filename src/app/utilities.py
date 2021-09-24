import decimal
import json
import requests

from threading import Thread
from datetime import date, datetime
from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_async_email(app, msg):

    with app.app_context():
        mail.send(msg)

def send_verification_email(email, token):
    '''
    Sends an email for verification of the email address when signing up

    Args:
        email (str): The email to send to
        token (str): The JWT token created for this verificaiton

    Returns:
        None
    '''
    msg = Message()

    msg.subject = "Verify Chained Metrics Email"
    msg.recipients = [email]
    msg.sender = 'serviceaccount@chainedmetrics.com'

    verify_url = current_app.config["URL"] + f"/verify?verifytoken={token}"

    msg.body = ('Thank you for signing up for Chained metrics. Please go to the below url '
                f'in your browser to verify your email\n\n{verify_url}')


    msg.html = (
        '<h1>Thank you for joining Chained Metrics!</h1>'
        '<p><a href="{verify_url}">Click here</a> to verify your email and begin trading KPIs! This link expires in 24 hours.</p>'
        f'<p>{verify_url}</p>'
    )

    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_resetpassword_email(email, token):
    '''
    Email used to reset a user's password

    Args:
        email (str): The email to send to
        token (str): The JWT token created for this verificaiton

    Returns:
        None
    '''

    msg = Message()

    msg.subject = "Reset Chained Metrics Password"
    msg.recipients = [email]
    msg.sender = 'serviceaccount@chainedmetrics.com'

    verify_url = current_app.config["URL"] + f"/resetpassword?resettoken={token}"

    msg.body = ('Follow the link below to reset your password. If you did not request this please email'
                ' us at info@chainedmetrics.com\n\n{verify_url}')


    msg.html = (
        '<h1><a href="{verify_url}">Click here</a> to reset your password.</h1> '
        '<p>If you did not request a password reset, email us at info@chainedmetrics.com</p>'
        f'<p>{verify_url}</p>'
    )

    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()


def subscribe_to_mailchimp_async(email):
    '''
    Async call to subscribe to Mailchimp with the email which happens when a user signs up

    Args:
        email (str): The email to signup with
    '''
    
    Thread(target=send_async_email, args=(email,)).start()


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

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):

        if isinstance(obj, date) or isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)

SWAGGER_TEMPLATE = {
    "swagger": "3.4.0",
    "info": {
        "title": "Chained Metrics API",
        "description": ("This is the backend API for all REST API calls. "
                        "For all requests that require authentication, "
                        "a JWT token needs to be added to the header. See the /auth/login endpoint for details"),
        "contact": {
        "responsibleOrganization": "ChainedMetrics",
        "responsibleDeveloper": "Michael Watson",
        "email": "michael@chainedmetrics.com"
        },
        "termsOfService": "https://chainedmetrics.com/termsofservice",
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {           # arbitrary name for the security scheme
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
}
