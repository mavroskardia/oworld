#
# Test class for new materials object
#

from items import Material

class TestMaterial:
    
    def test_constructor(self):
        material = Material()
        assert material is not None
        material = Material(name='Test Material')
        assert material is not None
        assert material.name == 'Test Material'
        
    def test_types(self):
        assert Material.Types.Blade == 'blade'
        assert Material.Types.Handle == 'handle'
        
    def test_properties(self):
        material = Material()
        # reads
        assert material.name == 'Unknown Material'
        assert material.value == 0
        assert material.durability == 0
        assert material.max_enhancements == 0
        assert material.can_be == ()        
        
        # writes
        name = 'Grass'
        material.name = name
        assert material.name == name
        
        value = 5
        material.value = value
        assert material.value == value
        
        durability = 2
        material.durability = durability
        assert material.durability == durability
        
        max_enhancements = 3
        material.max_enhancements = max_enhancements
        assert material.max_enhancements == max_enhancements

        can_be = (Material.Types.Blade, Material.Types.Handle)
        material.can_be = can_be
        assert material.can_be == can_be