from gateways.base_gateway import BaseGateway
import os
from models.order_model import OrderModel
from gateways.product_gateway import ProductGateway

class OrderGateway(BaseGateway):
    def __init__(self):
        super().__init__(os.environ['ORDER_TABLE_NAME'], id_field='order_id')
        self.product_gateway = ProductGateway()
    
    def create_order(self, order_data):
        """Create a new order with validation and inventory check"""
        # Create the order model
        order_model = OrderModel(order_data)
        
        # Validate basic order data
        errors = order_model.validate()
        if errors:
            return {'errors': errors}
        
        # Get user information for shipping address
        if 'shipping_address' not in order_model.order_data:
            from gateways.user_gateway import UserGateway
            user_gateway = UserGateway()
            user = user_gateway.get_by_id(order_model.order_data['user_id'])
            if user and 'address' in user:
                order_model.order_data['shipping_address'] = user['address']
            else:
                return {'errors': ['User address not found. Please update your profile or provide a shipping address.']}
        
        # Calculate prices and total amount
        calculation_errors = self._calculate_order_total(order_model.order_data)
        if calculation_errors:
            return {'errors': calculation_errors}
        
        # Check inventory and update product stock
        inventory_errors = self._check_and_update_inventory(order_model.order_data['items'])
        if inventory_errors:
            return {'errors': inventory_errors}
        
        # Create the order
        return self.create(order_model.order_data)
    
    def get_user_orders(self, user_id):
        """Get all orders for a specific user"""
        return self.query_by_attribute('user_id', user_id)
    
    def _check_and_update_inventory(self, items):
        """Check if items are in stock and update inventory"""
        errors = []
        
        # Create a list to track inventory updates
        inventory_updates = []
        
        # Check each product's availability
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get the product
            product = self.product_gateway.get_by_id(product_id)
            if not product:
                errors.append(f"Product with ID {product_id} not found")
                continue
            
            # Check if in stock (using quantity field)
            if 'quantity' not in product or product['quantity'] < quantity:
                errors.append(f"Not enough stock for product {product.get('name', product_id)}")
                continue
            
            # Track inventory update
            new_quantity = product['quantity'] - quantity
            inventory_updates.append({'product_id': product_id, 'quantity': new_quantity})
        
        # If no errors, update all inventory at once
        if not errors:
            for update in inventory_updates:
                self.product_gateway.update(update['product_id'], {'quantity': update['quantity']})
        
        return errors
    
    def _calculate_order_total(self, order_data):
        """Calculate total amount based on product prices"""
        errors = []
        total = 0
        
        # Get product prices and update items
        for item in order_data['items']:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get product details
            product = self.product_gateway.get_by_id(product_id)
            if not product:
                errors.append(f"Product with ID {product_id} not found")
                continue
                
            # Get price from product
            if 'price' not in product:
                errors.append(f"Price not found for product {product.get('name', product_id)}")
                continue
                
            # Calculate item total and add to order
            price = product['price']
            item['price'] = price  # Add price to the item
            item['subtotal'] = price * quantity  # Add subtotal to the item
            
            # Add to total
            total += item['subtotal']
            
        # If no errors, set the total
        if not errors:
            # Convert to Decimal for DynamoDB compatibility
            from decimal import Decimal
            order_data['total_amount'] = Decimal(str(total))
            
        return errors