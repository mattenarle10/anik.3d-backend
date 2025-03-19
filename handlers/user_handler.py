import json
import os
from models.user_model import UserModel
from gateways.user_gateway import UserGateway
from handlers.utils_handler import generate_response
import jwt

user_gateway = UserGateway()

def register(event, context):
    """Register a new user"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Create user
        result = user_gateway.create_user(body)
        
        # Check for errors
        if result.get('errors'):
            return generate_response(400, {'errors': result.get('errors')})
        
        # Return success
        return generate_response(201, {
            'message': 'User created successfully',
            'user': UserModel(result).to_json()
        })
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def login(event, context):
    """Login a user"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return generate_response(400, {'error': 'Email and password are required'})
        
        # Authenticate user
        auth_result = user_gateway.authenticate(email, password)
        if not auth_result:
            return generate_response(401, {'error': 'Invalid email or password'})
        
        # Return token
        return generate_response(200, auth_result)
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def get_all(event, context):
    """Get all users - Admin only"""
    try:
        
        # Get all users
        users = user_gateway.get_all()
        
        # Convert to JSON compatible format
        users_json = [UserModel(user).to_json() for user in users]
        
        return generate_response(200, users_json)
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def get_orders(event, context):
    """Get orders for the authenticated user"""
    try:
        # Extract user_id from the JWT token
        user_id = _get_user_id_from_token(event)
        if not user_id:
            return generate_response(401, {'error': 'Unauthorized'})
            
        # This will be implemented when we create the order functionality
        return generate_response(200, {'message': 'Order functionality coming soon'})
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def _get_user_id_from_token(event):
    """Extract user_id from JWT token"""
    try:
        auth_header = event.get('headers', {}).get('Authorization')
        if not auth_header:
            return None
            
        token = auth_header.replace('Bearer ', '')
        payload = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
        return payload.get('user_id')
    except:
        return None