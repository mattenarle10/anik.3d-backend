from models.base_model import BaseModel

class InventoryModel(BaseModel):
    def __init__(self, inventory_data=None):
        self.inventory_data = inventory_data or {}
        
    def validate(self):
        """Validate inventory data"""
        pass