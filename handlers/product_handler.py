import json
import os
import base64
from models.product_model import ProductModel
from gateways.product_gateway import ProductGateway
from handlers.utils_handler import generate_response
import boto3
import uuid

# Initialize the product gateway
product_gateway = ProductGateway()

def create(event, context):
    """Create a new product with optional 3D model file"""
    try:
        # Parse request body    
        body = json.loads(event.get('body', '{}'))
        
        # Check for file content in base64 format
        file_content = None
        file_name = None
        if 'model_file' in body and 'file_name' in body:
            file_content = base64.b64decode(body['model_file'])
            file_name = body['file_name']
            # Remove file data from body to avoid storing in DynamoDB
            del body['model_file']
            del body['file_name']
        
        # Set default category if not provided
        if 'category' not in body:
            body['category'] = 'default'
            
        # Validate product data
        product_model = ProductModel(body)
        validation_errors = product_model.validate()
        if validation_errors:
            return generate_response(400, {"errors": validation_errors})
        
        # Create product with optional file
        if file_content and file_name:
            result = product_gateway.create_with_model_file(
                product_model.to_dict(), 
                file_content, 
                file_name
            )
        else:
            result = product_gateway.create(product_model.to_dict())
        
        return generate_response(201, result)
    
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def get_all(event, context):
    """Get all products"""
    try:
        products = product_gateway.get_all()
        return generate_response(200, products)
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def get_by_id(event, context):
    """Get product by ID or name"""
    try:
        # Extract identifier from path parameter
        identifier = event.get('pathParameters', {}).get('id')
        if not identifier:
            return generate_response(400, {"error": "Product identifier is required"})
            
        # URL decode the identifier in case it contains spaces or special characters
        import urllib.parse
        identifier = urllib.parse.unquote(identifier)
        
        # Check query parameters for type of lookup
        query_params = event.get('queryStringParameters', {}) or {}
        lookup_type = query_params.get('type', 'auto').lower()
        
        product = None
        
        # Check if it's a UUID format (contains hyphens in the correct pattern)
        is_uuid_format = '-' in identifier and len(identifier.replace('-', '')) == 32
        
        # Auto-detect or use specified lookup type
        if lookup_type == 'name' or (lookup_type == 'auto' and not is_uuid_format and not identifier.isalnum()):
            # Look up by name
            product = product_gateway.get_by_name(identifier)
            if not product:
                return generate_response(404, {"error": f"Product with name '{identifier}' not found"})
        else:
            # Look up by ID (including UUID format)
            product = product_gateway.get_by_id(identifier)
            if not product:
                return generate_response(404, {"error": f"Product with ID '{identifier}' not found"})
        
        return generate_response(200, product)
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def update(event, context):
    """Update product"""
    try:
        # Extract product_id from path parameter
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            return generate_response(400, {"error": "Product ID is required"})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Check if product exists
        existing_product = product_gateway.get_by_id(product_id)
        if not existing_product:
            return generate_response(404, {"error": f"Product with ID {product_id} not found"})
        
        # Create a ProductModel to handle Decimal conversion for price
        # This ensures any price update is properly converted to Decimal
        if 'price' in body:
            from decimal import Decimal
            body['price'] = Decimal(str(body['price']))
        
        # Update product
        updated_product = product_gateway.update(product_id, body)
        
        return generate_response(200, updated_product)
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def delete(event, context):
    """Delete product"""
    try:
        # Extract product_id from path parameter
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            return generate_response(400, {"error": "Product ID is required"})
        
        # Check if product exists
        existing_product = product_gateway.get_by_id(product_id)
        if not existing_product:
            return generate_response(404, {"error": f"Product with ID {product_id} not found"})
        
        # Delete product
        deleted_product = product_gateway.delete(product_id)
        
        return generate_response(200, {"message": f"Product {product_id} deleted successfully"})
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def _is_admin(event):
    """Check if the request is from an admin"""
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

def is_admin(user):
    """Check if user is an admin"""
    if user:
        return user.get('is_admin', False)
    
    return False

def generate_upload_url(event, context):
    """Generate a presigned URL for direct S3 upload"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        if not file_name:
            return generate_response(400, {"error": "fileName is required"})
        
        # Generate a unique file key
        file_key = f"models/{uuid.uuid4()}-{file_name}"
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Generate presigned URL for PUT operation
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': os.environ['S3_BUCKET_NAME'],
                'Key': file_key,
                'ContentType': file_type or 'model/gltf-binary'
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        # Return the presigned URL and file details
        return generate_response(200, {
            'uploadUrl': presigned_url,
            'fileKey': file_key,
            'modelUrl': f"https://{os.environ['S3_BUCKET_NAME']}.s3.amazonaws.com/{file_key}"
        })
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in generate_upload_url: {str(e)}\n{error_details}")
        return generate_response(500, {"error": str(e)})