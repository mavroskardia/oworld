#
# Item Name Generator Tests
#

import py.test
from items import ItemNameGenerator, Template, Material

class TestItemNameGenerator:
    
    def test_constructor(self):
        py.test.raises(TypeError, "ItemNameGenerator()")        
        py.test.raises(TypeError, "ItemNameGenerator(None, None)")
                
        gen = ItemNameGenerator(Template(), [])        
        assert gen is not None
    
    def test_properties(self):
        pass
    
    def test_generate_name(self):
        template = Template(name='Dagger', required_level=3, primary_type=Material.Types.Handle, secondary_type=Material.Types.Blade)
        materials = [Material(name='Grass', can_be=(Material.Types.Blade, Material.Types.Blade)), Material(name='Pine', can_be=Material.Types.Handle)]
        gen = ItemNameGenerator(template, materials)
        name = gen.generate_name()
        
        assert name == 'Pine-handled Grass Dagger'
        