from flask import Blueprint, jsonify, request, Response
from .models import RequestAccess, db


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/requestaccess', methods=['POST'])
def metrics():
    '''
    Endpoint for requesting access to the Exchange UI

    This endpoint is used to request access to chainedmetrics.com
    ---

    consumes: 
      - application/json
    
    parameters:
      - in: body
        name: requestaccess
        description: DESC
        schema: 
          type: object
          required:
            - email
              full_name
          properties:
            email:
              type: string
            full_name:
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

        request_access = RequestAccess(full_name=full_name, email=email, reason=reason, company=company)
        db.session.add(request_access)
        db.session.commit()
        
        return Response('Success', 200)
    
    else:

        return Response("Email and full_name cannot be null", 400)