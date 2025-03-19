from models.base_model import BaseModel
import uuid
import re
import hashlib
import os
import json
import base64

class UserModel(BaseModel):
    def __init__(self, user_data=None):
        self.user_data = user_data or {}
        
        # If user_id is not provided, generate one
        if 'user_id' not in self.user_data:
            self.user_data['user_id'] = str(uuid.uuid4())
        
        # Hash password if it's a new user
        if 'password' in self.user_data and not self.user_data.get('password_hash'):
            self._hash_password()
            
    def _hash_password(self):
        """Hash the password and store the hash"""
        password = self.user_data.pop('password')
        # Generate a random salt
        salt = os.urandom(32)
        # Store the salt with the password hash
        self.user_data['salt'] = base64.b64encode(salt).decode('utf-8')
        # Create the hash
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # 100,000 iterations
        )
        self.user_data['password_hash'] = base64.b64encode(key).decode('utf-8')
    
    def verify_password(self, password):
        """Verify a password against the stored hash"""
        if 'password_hash' not in self.user_data or 'salt' not in self.user_data:
            return False
        
        # Get the stored salt
        salt = base64.b64decode(self.user_data['salt'])
        # Hash the provided password with the same salt
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Same number of iterations as in _hash_password
        )
        # Compare the hashes
        new_hash = base64.b64encode(key).decode('utf-8')
        return self.user_data['password_hash'] == new_hash
            
    def validate(self):
        """Validate user data"""
        errors = []
        
        # Required fields
        required_fields = ['email', 'name']
        for field in required_fields:
            if field not in self.user_data:
                errors.append(f"'{field}' is required")
        
        # Email validation
        if 'email' in self.user_data:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, self.user_data['email']):
                errors.append("Invalid email format")
        
        # Password validation for new users (if password is provided)
        if 'password' in self.user_data and len(self.user_data['password']) < 8:
            errors.append("Password must be at least 8 characters long")
        
        return errors
        
    def to_json(self):
        """Return a JSON-serializable dictionary of user data without sensitive fields"""
        user_data = self.user_data.copy()
        
        # Remove sensitive information
        if 'password_hash' in user_data:
            del user_data['password_hash']
        
        return user_data