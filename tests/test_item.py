#
# Tests for Overworld character inventory
#

import sys
sys.path.append('../components')

import py.test

from items import NewItem as Item
from items import Material

class Test_Item:
    
    def setup_class(cls):
        cls.item = Item()
    
    def test_constructor(self):
        assert self.item is not None

    def test_properties(self):        
        # reads
        assert self.item.name == 'Unknown Item'
        
        assert type(self.item.materials) is tuple
        assert len(self.item.materials) == 0
        
        assert self.item.value == 0
        
        # writes
        name = 'Grass Dagger'
        self.item.name = name
        assert self.item.name == name  
        
        material = Material(name='Grass')
        py.test.raises(Exception, "self.item.materials.append(material)")
        
    def test_add_material(self):
        material = Material()
        self.item.add_material(material)
        
        assert self.item.materials[0] == material
        assert len(self.item.materials) == 1