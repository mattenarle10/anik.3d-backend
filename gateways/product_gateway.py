from gateways.base_gateway import BaseGateway
import os
import boto3
import uuid

class ProductGateway(BaseGateway):
    def __init__(self):
        super().__init__(os.environ['PRODUCTS_TABLE_NAME'], id_field='product_id')
        self.s3 = boto3.client('s3')
        self.bucket_name = os.environ['S3_BUCKET_NAME']
    
    def create_with_model_file(self, product_data, file_content=None, file_name=None):
        """Create a product with an optional 3D model file"""
        if file_content and file_name:
            # Generate S3 key for the file
            file_key = f"models/{uuid.uuid4()}-{file_name}"
            
            # Upload file to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType='model/gltf-binary'  # Proper MIME type for GLB files
            )
            
            # Set the model_url in the product data
            product_data['model_url'] = f"https://{self.bucket_name}.s3.amazonaws.com/{file_key}"
        
        # Create the product in DynamoDB
        return self.create(product_data)
    
    def get_by_name(self, name):
        """Get product by name"""
        return self.query_by_attribute('name', name)
    
    def update_stock(self, product_id, quantity_change):
        """Update the stock quantity of a product"""
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        current_quantity = int(product.get('quantity', 0))
        new_quantity = max(0, current_quantity + quantity_change)  # Prevent negative quantities
        
        return self.update(product_id, {'quantity': new_quantity})