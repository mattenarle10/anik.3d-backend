import json
import base64
from gateways.order_gateway import OrderGateway
from handlers.utils_handler import generate_response, extract_user_from_token
from decimal import Decimal

# Initialize gateway
order_gateway = OrderGateway()

def create(event, context):
    """Create a new order"""
    try:
        # Extract user from token
        user = extract_user_from_token(event)
        if not user:
            return generate_response(401, {"error": "Unauthorized. Authentication required."})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Add user_id to order data
        body['user_id'] = user.get('user_id')
        
        # Check for file content in base64 format
        file_content = None
        file_name = None
        
        if 'custom_model_file' in body and 'file_name' in body:
            try:
                file_content = base64.b64decode(body['custom_model_file'])
                file_name = body['file_name']
                # Remove file data from body to avoid storing in DynamoDB
                del body['custom_model_file']
                del body['file_name']
            except Exception as e:
                return generate_response(400, {"error": f"Invalid base64 encoding: {str(e)}"})
        
        # Create the order with server-side price calculation and user address
        if file_content and file_name:
            result = order_gateway.create_order_with_model(body, file_content, file_name)
        else:
            result = order_gateway.create_order(body)
        
        # Check for errors
        if 'errors' in result:
            return generate_response(400, {"errors": result['errors']})
        
        # Convert Decimal objects for JSON serialization
        order = _convert_decimal(result)
        
        return generate_response(201, {
            "message": "Order created successfully",
            "order": order
        })
    
    except Exception as e:
        # Handle binary data in error messages
        error_msg = "Error processing request"
        try:
            error_msg = str(e)
        except:
            pass
        return generate_response(500, {"error": error_msg})

def get_user_orders(event, context):
    """Get orders for the authenticated user"""
    try:
        # Extract user from token
        user = extract_user_from_token(event)
        if not user:
            return generate_response(401, {"error": "Unauthorized. Authentication required."})
        
        # Get user orders (already sanitized in the gateway)
        user_id = user.get('user_id')
        orders = order_gateway.get_user_orders(user_id)
        
        return generate_response(200, orders)
    
    except Exception as e:
        # Handle binary data in error messages
        error_msg = "Error retrieving orders"
        try:
            error_msg = str(e)
        except:
            pass
        return generate_response(500, {"error": error_msg})

def get_all(event, context):
    """Get all orders (admin function)"""
    try:
        # Get all orders (already sanitized in the gateway)
        orders = order_gateway.get_all()
        
        return generate_response(200, orders)
    
    except Exception as e:
        # Handle binary data in error messages
        error_msg = "Error retrieving orders"
        try:
            error_msg = str(e)
        except:
            pass
        return generate_response(500, {"error": error_msg})

def update_status(event, context):
    """Update order status (admin function)"""
    try:
       
        # Extract order_id from path parameter
        order_id = event.get('pathParameters', {}).get('id')
        if not order_id:
            return generate_response(400, {"error": "Order ID is required"})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get new status from request body
        new_status = body.get('status')
        if not new_status:
            return generate_response(400, {"error": "status is required in the request body"})
        
        # Valid status values
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return generate_response(400, {
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        # Check if order exists
        existing_order = order_gateway.get_by_id(order_id)
        if not existing_order:
            return generate_response(404, {"error": f"Order with ID {order_id} not found"})
        
        # Update order status
        updated_order = order_gateway.update(order_id, {"status": new_status})
        
        # Convert any Decimal objects to float for JSON serialization
        updated_order = _convert_decimal(updated_order)
        
        if updated_order:
            return generate_response(200, {
                "message": f"Order status updated to {new_status}",
                "order": updated_order
            })
        else:
            return generate_response(500, {"error": f"Failed to update status for order {order_id}"})
    
    except Exception as e:
        # Handle binary data in error messages
        error_msg = "Error processing request"
        try:
            error_msg = str(e)
        except:
            pass
        return generate_response(500, {"error": error_msg})

def delete_order(event, context):
    """Delete an order (admin only)"""
    try:
        # Get order ID from path parameters
        order_id = event.get('pathParameters', {}).get('id')
        if not order_id:
            return generate_response(400, {"error": "Order ID is required"})
        
        # Delete the order
        result = order_gateway.delete_order(order_id)
        
        # Check for errors
        if 'error' in result:
            return generate_response(404, {"error": result['error']})
        
        return generate_response(200, {"message": "Order deleted successfully"})
    except Exception as e:
        return generate_response(500, {"error": f"Server error: {str(e)}"})

def generate_upload_url(event, context):
    """Generate a presigned URL for direct S3 upload"""
    try:
        # Extract the token from the Authorization header
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header:
            return generate_response(401, {'error': 'No authorization token provided'})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        # Check if this is a request for multiple files
        is_multiple = body.get('isMultiple', False)
        file_count = body.get('fileCount', 1) if is_multiple else 1
        
        if not file_name:
            return generate_response(400, {"error": "fileName is required"})
        
        # Generate a unique file key
        import uuid
        import os
        import boto3
        
        # Create S3 client
        s3_client = boto3.client('s3')
        bucket_name = os.environ['S3_BUCKET_NAME']
        
        if is_multiple:
            # Generate multiple presigned URLs
            upload_urls = []
            model_urls = []
            file_keys = []
            
            for i in range(file_count):
                # Generate unique file key for each file
                # Use index suffix for multiple files
                indexed_file_name = f"{os.path.splitext(file_name)[0]}_{i}{os.path.splitext(file_name)[1]}" if file_count > 1 else file_name
                file_key = f"orders/{uuid.uuid4()}-{indexed_file_name}"
                file_keys.append(file_key)
                
                # Generate presigned URL for this file
                presigned_url = s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': file_key,
                        'ContentType': file_type
                    },
                    ExpiresIn=3600  # URL expires in 1 hour
                )
                
                upload_urls.append(presigned_url)
                model_urls.append(f"https://{bucket_name}.s3.amazonaws.com/{file_key}")
            
            return generate_response(200, {
                "uploadUrls": upload_urls,
                "modelUrls": model_urls,
                "fileKeys": file_keys
            })
        else:
            # Original single file logic
            file_key = f"orders/{uuid.uuid4()}-{file_name}"
            
            # Generate a presigned URL for uploading directly to S3
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_key,
                    'ContentType': file_type
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            
            return generate_response(200, {
                "uploadUrl": presigned_url,
                "modelUrl": f"https://{bucket_name}.s3.amazonaws.com/{file_key}",
                "fileKey": file_key
            })
    except Exception as e:
        return generate_response(500, {"error": f"Server error: {str(e)}"})

def _json_safe_encoder(obj):
    """Handle non-JSON serializable objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (bytes, bytearray, memoryview)):
        return None  # Skip binary data
    elif hasattr(obj, 'isoformat'):  # Handle date/datetime objects
        return obj.isoformat()
    else:
        return str(obj)  # Convert other non-serializable objects to string

def _convert_decimal(obj):
    """Convert a single item's Decimal values to float and handle binary data"""
    import base64
    from botocore.response import StreamingBody
    
    if isinstance(obj, dict):
        return {k: float(v) if isinstance(v, Decimal) 
                else base64.b64encode(v).decode('utf-8') if isinstance(v, (bytes, bytearray, memoryview, StreamingBody))
                else _convert_decimal(v) if isinstance(v, (dict, list)) 
                else v 
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimal(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (bytes, bytearray, memoryview, StreamingBody)):
        return base64.b64encode(obj).decode('utf-8')
    else:
        return obj