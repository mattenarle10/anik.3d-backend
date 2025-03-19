from models.base_model import BaseModel
import uuid
from datetime import datetime
import json

class OrderModel(BaseModel):
    def __init__(self, order_data=None):
        self.order_data = order_data or {}
        # Generate order_id if not present
        if self.order_data and 'order_id' not in self.order_data:
            self.order_data['order_id'] = str(uuid.uuid4())
            
        # Set creation timestamp if new order
        if self.order_data and 'created_at' not in self.order_data:
            self.order_data['created_at'] = datetime.utcnow().isoformat()
            
        # Set initial status if not provided
        if self.order_data and 'status' not in self.order_data:
            self.order_data['status'] = 'pending'
            
    def validate(self):
        """Validate order data"""
        errors = []
        # Only require user_id and items - other fields will be calculated/retrieved
        required_fields = ['user_id', 'items']
        
        # Check for required fields
        for field in required_fields:
            if field not in self.order_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate items structure if present
        if 'items' in self.order_data:
            if not isinstance(self.order_data['items'], list):
                errors.append("Items must be a list")
            else:
                for index, item in enumerate(self.order_data['items']):
                    if not isinstance(item, dict):
                        errors.append(f"Item at index {index} must be an object")
                    elif 'product_id' not in item:
                        errors.append(f"Item at index {index} missing product_id")
                    elif 'quantity' not in item:
                        errors.append(f"Item at index {index} missing quantity")
                    elif not isinstance(item.get('quantity'), (int, float)) or item.get('quantity') <= 0:
                        errors.append(f"Item at index {index} has invalid quantity")
        
        # Validate total_amount is a positive number if present
        if 'total_amount' in self.order_data:
            if not isinstance(self.order_data['total_amount'], (int, float)) or self.order_data['total_amount'] <= 0:
                errors.append("Total amount must be a positive number")
        
        return errors
    
    def to_json(self):
        """Convert to JSON-serializable format without sensitive data"""
        return self.order_data