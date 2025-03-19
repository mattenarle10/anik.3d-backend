import json
from gateways.base_gateway import DecimalEncoder

def generate_response(status_code, body):
    """Generate standardized API response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def extract_user_from_token(event):
    """Extract and validate user from JWT token in request headers"""
    import jwt
    import os
    
    # Get the token from the authorization header
    # Check both 'Authorization' and 'authorization' due to API Gateway case sensitivity
    headers = event.get('headers', {})
    if not headers:
        return None
        
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if not auth_header:
        return None
        
    # Check if the auth header starts with 'Bearer '
    if not auth_header.startswith('Bearer '):
        return None
        
    # Extract the token
    token = auth_header.split(' ')[1]
    
    try:
        # Decode the token
        decoded = jwt.decode(token, os.environ.get('JWT_SECRET'), algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None