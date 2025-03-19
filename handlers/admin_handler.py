import os
import json
import base64
from handlers.utils_handler import generate_response

def login(event, context):
    """Admin login with fixed credentials"""
    try:
        # Get admin credentials from environment variables
        admin_id = os.environ.get('ADMIN_ID')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get credentials from request
        username = body.get('username')
        password = body.get('password')
        
        # Check credentials
        if not username or not password:
            return generate_response(400, {"error": "Username and password are required"})
        
        if username == admin_id and password == admin_password:
            return generate_response(200, {
                "message": "Login successful",
                "admin_id": admin_id
            })
        else:
            return generate_response(401, {"error": "Invalid credentials"})
    
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def verify_admin(event):
    """Verify admin credentials from Authorization header"""
    # Get admin credentials from environment variables
    admin_id = os.environ.get('ADMIN_ID')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    # Get Authorization header
    auth_header = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
    
    if not auth_header:
        return False
    
    # Check if it's Basic auth
    if auth_header.startswith('Basic '):
        try:
            # Decode base64 credentials
            credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = credentials.split(':')
            
            # Check against admin credentials
            return username == admin_id and password == admin_password
        except Exception:
            return False
    
    return False