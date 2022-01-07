import os

from flask import Blueprint, jsonify, request
from datetime import timedelta
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy.exc import IntegrityError

from .models import User, MaticFaucetQueue, db
from .auth import jwt


faucet_bp = Blueprint('faucet', __name__)


@faucet_bp.route('/requestmatic', methods=['POST'])
@jwt_required()
def user():
    '''
    A one time request of MATIC for this account
    This is a one time requst for MATIC for this account. The address will be stored for future notification and associated with this account

    It does require an valid token to be in the header in order to see this information
    ---
    security:
        - bearerAuth: []
    requestBody:
        required: true
        description: Required fields for the faucet
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        address:
                            type: string

    responses:
        200:
            description: The request has been submitted successfully
        400:
            description: User has already recieved MATIC or other issue. See message
        401:
            description: Invalid token
        406:
            description: User already recieved MATIC
    '''
    
    address = request.json.get('address')
    if not address or not isinstance(address, str) or len(address) != 42:
        return jsonify(message='Invalid or address'), 400
    
    elif current_user.matic_recieved:
        return jsonify(message='User already recieved matic'), 406
    
    elif not current_user.active:
        return jsonify(message='User has not verified email address'), 406

    else:
        try:
            queue_entry = MaticFaucetQueue(
                email=current_user.email,
                address=address
            )

            db.session.add(queue_entry)
            db.session.execute(f"NOTIFY faucet_request, '{current_user.email}';")
            db.session.commit()

            return jsonify(message="Successfully requested Matic Faucet"), 200

        except IntegrityError:
            return jsonify(message='Request is already pending. If problem persists over 24hrs message us on Discord'), 406
