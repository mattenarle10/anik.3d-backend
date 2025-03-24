from gateways.base_gateway import BaseGateway
import os
import boto3
import uuid
from models.order_model import OrderModel
from gateways.product_gateway import ProductGateway
from decimal import Decimal

class OrderGateway(BaseGateway):
    def __init__(self):
        super().__init__(os.environ['ORDER_TABLE_NAME'], id_field='order_id')
        self.product_gateway = ProductGateway()
        self.s3 = boto3.client('s3')
        self.bucket_name = os.environ['S3_BUCKET_NAME']
    
    def create_order_with_model(self, order_data, file_content=None, file_name=None):
        """Create a new order with validation, inventory check, and optional model file"""
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
        
        # Handle custom model file upload if provided
        if file_content and file_name:
            try:
                # Generate S3 key for the file
                file_key = f"order_models/{order_model.order_data['order_id']}/{uuid.uuid4()}-{file_name}"
                
                # Upload file to S3
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=file_content,
                    ContentType='model/gltf-binary'  # Proper MIME type for GLB files
                )
                
                # Set the custom_model_url in the order data
                order_model.order_data['custom_model_url'] = f"https://{self.bucket_name}.s3.amazonaws.com/{file_key}"
                
            except Exception as e:
                return {'errors': [f"Error uploading custom model file: {str(e)}"]}
        
        # Create the order
        return self.create(order_model.order_data)
    
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
    
    def create_order_with_model_url(self, order_data, custom_model_url, file_name):
        """Create a new order with a custom model URL (already uploaded to S3)"""
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
        
        # Store the custom model URL in the order data
        order_model.order_data['custom_model'] = custom_model_url
        
        # Create the order
        return self.create(order_model.order_data)
    
    def create_order_with_multiple_models(self, order_data, custom_model_urls, file_names):
        """Create a new order with multiple custom model URLs (already uploaded to S3)"""
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
        
        # Store the custom model URLs in the order data
        if len(custom_model_urls) == 1:
            # If there's only one URL, store it in the custom_model field for backward compatibility
            order_model.order_data['custom_model'] = custom_model_urls[0]
        
        # Always store the array of URLs in custom_models field
        order_model.order_data['custom_models'] = custom_model_urls
        
        # Create the order
        return self.create(order_model.order_data)
    
    def get_user_orders(self, user_id):
        """Get all orders for a specific user"""
        orders = self.query_by_attribute('user_id', user_id)
        return self._sanitize_orders(orders)
    
    def get_all(self):
        """Get all orders with binary data removed"""
        orders = super().get_all()
        return self._sanitize_orders(orders)
    
    def _sanitize_orders(self, orders):
        """Remove any binary data from orders to ensure JSON serialization works"""
        sanitized_orders = []
        for order in orders:
            sanitized_order = {}
            for key, value in order.items():
                if isinstance(value, (bytes, bytearray, memoryview)):
                    # Skip binary data
                    continue
                elif isinstance(value, dict):
                    # Handle nested dictionaries
                    sanitized_order[key] = {k: v for k, v in value.items() 
                                          if not isinstance(v, (bytes, bytearray, memoryview))}
                elif isinstance(value, list):
                    # Handle lists
                    sanitized_order[key] = []
                    for item in value:
                        if isinstance(item, dict):
                            sanitized_order[key].append({k: v for k, v in item.items()
                                                      if not isinstance(v, (bytes, bytearray, memoryview))})
                        elif not isinstance(item, (bytes, bytearray, memoryview)):
                            sanitized_order[key].append(item)
                else:
                    sanitized_order[key] = value
            sanitized_orders.append(sanitized_order)
        return sanitized_orders
    
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
        total_customization = 0
        
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
            
            # Handle customization price if present
            customization_price = 0
            if 'price_adjustment' in item and item['price_adjustment']:
                try:
                    customization_price = Decimal(str(item['price_adjustment']))
                    # Track total customization cost
                    total_customization += customization_price * quantity
                except (ValueError, TypeError):
                    errors.append(f"Invalid customization price for product {product.get('name', product_id)}")
            
            # Calculate subtotal including customization
            item_price_with_customization = price + customization_price
            item['subtotal'] = item_price_with_customization * quantity  # Add subtotal to the item
            
            # Add to total
            total += item['subtotal']
            
        # If no errors, set the total
        if not errors:
            # Store customization amount if present
            if total_customization > 0:
                order_data['customization_amount'] = total_customization
            
            # Calculate tax if needed (8.5%)
            if 'include_tax' in order_data and order_data['include_tax']:
                tax_rate = Decimal('0.085')  # 8.5% tax
                tax_amount = total * tax_rate
                order_data['tax_amount'] = tax_amount
                total += tax_amount
            
            # Convert to Decimal for DynamoDB compatibility
            order_data['total_amount'] = Decimal(str(total))
            
        return errors
    
    def delete_order(self, order_id):
        """Delete an order (admin only)"""
        # First check if the order exists
        order = self.get_by_id(order_id)
        if not order:
            return {'error': f'Order with ID {order_id} not found'}
        
        # Delete the order
        result = self.delete(order_id)
        
        # If the order had a custom model, delete it from S3
        if 'custom_model_url' in order:
            try:
                # Extract the key from the URL
                url_parts = order['custom_model_url'].split('/')
                key = '/'.join(url_parts[3:])  # Skip https://bucket-name.s3.amazonaws.com/
                
                # Delete the file from S3
                self.s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            except Exception as e:
                # Log the error but don't fail the order deletion
                print(f"Error deleting custom model file: {str(e)}")
        
        return {'message': 'Order deleted successfully'}