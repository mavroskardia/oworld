#
# Tests for Overworld character inventory
#

import sys
sys.path.append('../components')

from items import NewInventory as Inventory
from items import NewItem as Item
from items import Material

class Test_Inventory:
    
    def setup_class(cls):
        cls.inv = Inventory()
    
    def test_construction(self):
        assert self.inv is not None
        
    def test_properties(self):
        assert type(self.inv.items) is tuple
        assert len(self.inv.items) == 0 
        
    def test_inventory_add_items(self):
        item = Item()
        item.add_material(Material())
        
        self.inv.add_item(item)