import os
import boto3
from decimal import Decimal
import json
import uuid

# Custom JSON encoder for handling Decimal values
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class BaseGateway:
    def __init__(self, table_name, id_field='id'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.id_field = id_field
    
    def create(self, item):
        """Create a new item"""
        # Ensure item has an ID
        if self.id_field not in item:
            item[self.id_field] = str(uuid.uuid4())
        
        # Insert into DynamoDB
        self.table.put_item(Item=item)
        return item
    
    def get_all(self):
        """Get all items from the table"""
        response = self.table.scan()
        return response.get('Items', [])
    
    def get_by_id(self, item_id):
        """Get item by ID"""
        response = self.table.get_item(
            Key={self.id_field: item_id}
        )
        return response.get('Item')
    
    def update(self, item_id, updates):
        """Update an item"""
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        
        for key, value in updates.items():
            if key != self.id_field:  # Don't update the primary key
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
        
        # Remove trailing comma and space
        if update_expression != "SET ":
            update_expression = update_expression[:-2]
            
            # Build expression attribute names
            expression_attribute_names = {f"#{k}": k for k in updates.keys() if k != self.id_field}
            
            response = self.table.update_item(
                Key={self.id_field: item_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            return response.get('Attributes')
        
        return self.get_by_id(item_id)  # No updates to apply
    
    def delete(self, item_id):
        """Delete an item"""
        response = self.table.delete_item(
            Key={self.id_field: item_id},
            ReturnValues="ALL_OLD"
        )
        return response.get('Attributes')
    
    def query_by_attribute(self, attribute_name, attribute_value):
        """Query items by a specific attribute"""
        response = self.table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr(attribute_name).eq(attribute_value)
        )
        return response.get('Items', [])