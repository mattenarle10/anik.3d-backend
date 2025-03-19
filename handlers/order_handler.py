import json
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
        
        # Create the order with server-side price calculation and user address
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
        return generate_response(500, {"error": str(e)})

def get_user_orders(event, context):
    """Get orders for the authenticated user"""
    try:
        # Extract user from token
        user = extract_user_from_token(event)
        if not user:
            return generate_response(401, {"error": "Unauthorized. Authentication required."})
        
        # Get user orders
        user_id = user.get('user_id')
        orders = order_gateway.get_user_orders(user_id)
        
        # Convert Decimal objects for JSON serialization
        orders = _convert_decimals(orders)
        
        return generate_response(200, orders)
    
    except Exception as e:
        return generate_response(500, {"error": str(e)})

def get_all(event, context):
    """Get all orders (admin function)"""
    try:
        # Get all orders
        orders = order_gateway.get_all()
        
        # Convert any Decimal objects to float for JSON serialization
        orders = _convert_decimals(orders)
        
        return generate_response(200, orders)
    
    except Exception as e:
        return generate_response(500, {"error": str(e)})

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
        return generate_response(500, {"error": str(e)})

def _convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [_convert_decimal(item) for item in obj]
    else:
        return _convert_decimal(obj)

def _convert_decimal(obj):
    """Convert a single item's Decimal values to float"""
    if isinstance(obj, dict):
        return {k: float(v) if isinstance(v, Decimal) else _convert_decimal(v) if isinstance(v, (dict, list)) else v 
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimal(item) for item in obj]
    else:
        return obj