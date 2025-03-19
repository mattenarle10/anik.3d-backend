from models.base_model import BaseModel
from decimal import Decimal
import json
import uuid
import re

class ProductModel(BaseModel):
    def __init__(self, product_data=None):
        self.product_data = product_data or {}
        
        # If product_id is not provided, generate one
        if 'product_id' not in self.product_data:
            self.product_data['product_id'] = str(uuid.uuid4())
            
        # Convert price to Decimal for DynamoDB compatibility if present
        if 'price' in self.product_data and not isinstance(self.product_data['price'], Decimal):
            self.product_data['price'] = Decimal(str(self.product_data['price']))
            
        # Ensure quantity is an integer if present
        if 'quantity' in self.product_data and not isinstance(self.product_data['quantity'], int):
            self.product_data['quantity'] = int(self.product_data['quantity'])
        
    def validate(self):
        """Validate product data"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'description', 'price']
        for field in required_fields:
            if field not in self.product_data or not self.product_data[field]:
                errors.append(f"Field '{field}' is required")
        
        # Price validation
        if 'price' in self.product_data:
            try:
                price = float(self.product_data['price'])
                if price < 0:
                    errors.append("Price cannot be negative")
            except (ValueError, TypeError):
                errors.append("Price must be a number")
        
        # Quantity validation
        if 'quantity' in self.product_data:
            try:
                quantity = int(self.product_data['quantity'])
                if quantity < 0:
                    errors.append("Quantity cannot be negative")
            except (ValueError, TypeError):
                errors.append("Quantity must be an integer")
        
        # 3D model URL validation if present
        if 'model_url' in self.product_data and self.product_data['model_url']:
            if not self._is_valid_s3_url(self.product_data['model_url']):
                errors.append("Model URL must be a valid S3 URL")
        
        return errors
    
    def _is_valid_s3_url(self, url):
        """Check if the URL is a valid S3 URL"""
        # Simple check for s3:// or https://s3 URLs
        return url.startswith('s3://') or 's3.amazonaws.com' in url
    
    def to_dict(self):
        """Convert model to dictionary"""
        return self.product_data
    
    def to_json(self):
        """Convert model to JSON string"""
        # Create a copy to avoid modifying the original
        data_copy = self.product_data.copy()
        
        # Convert Decimal to float for JSON serialization
        for key, value in data_copy.items():
            if isinstance(value, Decimal):
                data_copy[key] = float(value)
        
        return json.dumps(data_copy)