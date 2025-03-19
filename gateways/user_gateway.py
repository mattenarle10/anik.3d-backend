from gateways.base_gateway import BaseGateway
import os
from models.user_model import UserModel
import jwt
from datetime import datetime, timedelta

class UserGateway(BaseGateway):
    def __init__(self):
        super().__init__(os.environ['USER_TABLE_NAME'], id_field='user_id')
        self.jwt_secret = os.environ['JWT_SECRET']
        
    def create_user(self, user_data):
        """Create a new user with validation"""
        user_model = UserModel(user_data)
        validation_errors = user_model.validate()
        
        if validation_errors:
            return {'errors': validation_errors}
        
        # Check if email already exists
        existing_user = self.get_by_email(user_data.get('email'))
        if existing_user:
            return {'errors': ['Email already registered']}
        
        # Create the user
        return self.create(user_model.user_data)
    
    def get_by_email(self, email):
        """Get user by email"""
        result = self.query_by_attribute('email', email)
        # Return the first user with the given email, or None if not found
        return result[0] if result else None
    
    def authenticate(self, email, password):
        """Authenticate a user and return a JWT token if successful"""
        user = self.get_by_email(email)
        if not user:
            return None
        
        # Verify password
        user_model = UserModel(user)
        if not user_model.verify_password(password):
            return None
        
        # Generate JWT token
        expiration = datetime.utcnow() + timedelta(days=7)
        token = jwt.encode({
            'user_id': user.get('user_id'),
            'email': user.get('email'),
            'name': user.get('name'),
            'is_admin': False,
            'exp': expiration
        }, self.jwt_secret, algorithm='HS256')
        
        return {
            'token': token,
            'user': user_model.to_json()
        }