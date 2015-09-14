#
# Test class for new materials object
#

from items import Template, Material

class TestTemplate:

    def test_constructor(self):
        template = Template()
        assert template is not None
        
        template = Template(name='Test Template')
        assert template is not None
        assert template.name == 'Test Template'
        
    def test_properties(self):
        template = Template()
        # reads
        assert template.name == 'Unknown Template'
        assert template.required_level == 0
        assert template.required_materials == []
        assert template.primary_type == None
        assert template.secondary_type == None
        
        # writes
        name = 'Grass'
        template.name = name
        assert template.name == name

        required_level = 3
        template.required_level = required_level
        assert template.required_level == required_level
        
        required_materials = [1,2]
        template.required_materials = required_materials
        assert template.required_materials == required_materials
        
        primary = Material.Types.Blade
        secondary = Material.Types.Handle
        template.primary_type = primary
        template.secondary_type = secondary
        assert template.primary_type == primary
        assert template.secondary_type == secondary
        