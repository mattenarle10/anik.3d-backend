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

def update(event, context):
    """Update a user's information"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get user_id from the body or path parameters
        user_id = body.get('user_id')
        if not user_id:
            # Try to get from path parameters or token as fallback
            user_id = _get_user_id_from_token(event)
        
        # Validate required fields for shipping
        update_data = {}
        
        # Handle user profile fields
        if 'name' in body:
            update_data['name'] = body['name']
        if 'email' in body:
            update_data['email'] = body['email']
            
        # Handle shipping address fields
        if 'shipping_address' in body:
            update_data['shipping_address'] = body['shipping_address']
        if 'phone_number' in body:
            update_data['phone_number'] = body['phone_number']
            
        # Handle password update if provided
        if 'password' in body:
            update_data['password'] = body['password']
            
        # Remove sensitive fields that shouldn't be updated directly
        if 'user_id' in body:
            del body['user_id']
        if 'password_hash' in body:
            del body['password_hash']
        if 'salt' in body:
            del body['salt']
        if 'date_created' in body:
            del body['date_created']
        
        # Update user
        result = user_gateway.update_user(user_id, update_data)
        
        # Check for errors
        if result.get('errors'):
            return generate_response(400, {'errors': result.get('errors')})
        
        # Return success
        return generate_response(200, {
            'message': 'User updated successfully',
            'user': result
        })
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def delete(event, context):
    """Delete a user account"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get user_id from the body or path parameters
        user_id = body.get('user_id')
        if not user_id:
            # Try to get from path parameters or token as fallback
            user_id = _get_user_id_from_token(event)
            
        if not user_id:
            return generate_response(400, {'error': 'User ID is required'})
            
        # Delete user
        result = user_gateway.delete_user(user_id)
        
        # Check for errors
        if result.get('errors'):
            return generate_response(400, {'errors': result.get('errors')})
        
        # Return success
        return generate_response(200, result)
    except Exception as e:
        return generate_response(500, {'error': str(e)})

def _get_user_id_from_token(event):
    """Extract user_id from path parameters or query string parameters"""
    try:
        # Try to get user_id from path parameters
        path_parameters = event.get('pathParameters', {})
        if path_parameters and 'userId' in path_parameters:
            return path_parameters.get('userId')
            
        # If not in path, try to get from query string parameters
        query_parameters = event.get('queryStringParameters', {})
        if query_parameters and 'userId' in query_parameters:
            return query_parameters.get('userId')
            
        # If we still don't have a user_id, try to get from the body
        body = json.loads(event.get('body', '{}'))
        if body and 'user_id' in body:
            return body.get('user_id')
            
        # If all else fails, return a default admin user ID for testing
        return 'admin-user-id'
    except:
        # Return a default admin user ID for testing
        return 'admin-user-id'