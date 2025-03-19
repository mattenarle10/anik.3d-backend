import json
from gateways.product_gateway import ProductGateway
from handlers.utils_handler import generate_response

# Initialize gateways
product_gateway = ProductGateway()

def update_stock(event, context):
    """Update product stock quantity"""
    try:
        # Extract product_id from path parameter
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            return generate_response(400, {"error": "Product ID is required"})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get quantity change from request body
        quantity_change = body.get('quantity_change')
        if quantity_change is None:
            return generate_response(400, {"error": "quantity_change is required in the request body"})
        
        try:
            quantity_change = int(quantity_change)
        except ValueError:
            return generate_response(400, {"error": "quantity_change must be an integer"})
        
        # Check if product exists
        existing_product = product_gateway.get_by_id(product_id)
        if not existing_product:
            return generate_response(404, {"error": f"Product with ID {product_id} not found"})
        
        # Update product stock by adding to existing quantity
        updated_product = product_gateway.update_stock(product_id, quantity_change)
        
        if updated_product:
            return generate_response(200, {
                "message": f"Stock updated successfully for product {product_id}",
                "previous_quantity": existing_product.get('quantity', 0),
                "quantity_added": quantity_change,
                "new_quantity": updated_product.get('quantity', 0),
                "product": updated_product
            })
        else:
            return generate_response(500, {"error": f"Failed to update stock for product {product_id}"})
    
    except Exception as e:
        return generate_response(500, {"error": str(e)})