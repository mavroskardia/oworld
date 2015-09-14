# items.py
# The loading, parsing, and displaying of item data in Overworld
# by Andrew Martin (2006)
#
# TODO:
#    [x] Comment all classes
#    [x] Rename members that don't adhere to style guidelines
#    [x] Review algorithms to determine if there is a more pythonic way
#    [x] Review classes included in module for relevance to module
#

import constants

class Item(object):
    "Class representing an item read from the item collection"
    
    def __init__(self, inventory, itemCollector):
        self.fullValue = 0
        self.inventory = inventory
        self.itemCollector = itemCollector
        self.image = None
        self.width = 1
        self.height = 1        
        self.name = "Default"
        self.depreciationFactor = 0.66        
        self.locations = 0
        self.types = 0
        self.jobs = constants.JobTypes.All
        self.attack = 0
        self.defense = 0
        self.attackBonus = 0
        self.defenseBonus = 0
        self.count = 1
        self.events = {}
        
    def __repr__(self): return self.name

    def __get_owner(self): return self.inventory.actor
    owner = property(__get_owner, None, None, "Get the item's current owner (retrieves it via the inventory that contains this item).")

    def __get_desc(self): return self.itemCollector.getDescription(self.name)
    description = property(__get_desc, None, None, "Get the item's description (retrieves it from the ItemCollector).")
    
    def __get_worth(self): return int(self.fullValue * self.depreciationFactor)
    worth = property(__get_worth, None, None, "Get the item's worth with depreciation factored in.")
    
    def drop(self): 
        self.count -= 1
        if self.count == 0: self.inventory.removeItem(self)
        self.itemCollector.scene.createMapContainer(self)

class Inventory(object):
    "The entry and exit point for all items, equipped or stowed, that an actor carries."
    
    def __init__(self, owner):
        self.actor = owner
        self.stowed = []
        self.equipped = {}
        
    def __repr__(self):
        return "%s's Inventory:\n\tEquipped: %s\n\tStowed: %s" % (self.actor.name, self.equipped, self.stowed)
        
    def stowItem(self, item, count=1):
        "Stow the specified item in the pack"
        
        if item in self.stowed: 
            print "Failed to add item: can't add same item twice"
            return
        
        for i in self.stowed:
            if item.name == i.name:
                # same-named item, just increment that item's count
                i.count += count
                break
        else: self.stowed.append(item) # no match, add
            
        if "onStow" in item.events: item.events["onStow"](self.actor, self.actor.scene)
            
    def equipItem(self, item):
        "Determines if item is equippable, then equips it to the appropriate location."

        if not self.canEquip(item): return False
        else:
            if self.equipped[item.equipLocation] != None:
                # take the current item off and stow it first
                currentItem = self.equipped[item.equipLocation]
                self.stowItem(item)
            
            self.equipped[item.equipLocation] = item
            if "onEquip" in item.events: item.events["onEquip"](self.actor, self.actor.scene)
            return True
        
    def canEquip(self, item):
        "Checks to see if this inventory's actor can equip the specified item."
        return self.actor.job in item.equippableJobs
    
    def removeItem(self, itm):
        """Removes the specified item from the inventory"""
        
        for item in self.stowed:
            if item.name == itm.name:
                if item.count > 1:
                    item.count -= 1
                else: 
                    self.stowed.remove(item)
                break

class Template(object):
    '''
    '''
    
    def __init__(self, **kwargs):
        self.name = 'Unknown Template'
        self.required_level = 0
        self.required_materials = []
        self.primary_type = None
        self.secondary_type = None
        
        for kw in kwargs:
            if hasattr(self, kw): setattr(self, kw, kwargs[kw])        

class Material(object):
    '''
    '''
    
    class Types:
        Blade = 'blade'
        Handle = 'handle'
        Blood = 'blood'
        
    def __init__(self, **kwargs):
        self.name = 'Unknown Material'
        self.value = 0
        self.durability = 0
        self.max_enhancements = 0
        self.can_be = ()
            
        for kw in kwargs: 
            if hasattr(self, kw): setattr(self, kw, kwargs[kw])            

class NewItem(object):
    '''
    '''

    def __init__(self):
        self.__materials = []
        self.name = 'Unknown Item'

    # privates        
    def __get_materials(self): return tuple(self.__materials)
    def __get_value(self): return 0
    
    # properties
    materials = property(__get_materials, None, None, 'Read-only collection of materials that makes up this item.')    
    value = property(__get_value, None, None, 'Read-only value of the item based on its materials')
    
    # methods
    def add_material(self, material):
        assert type(material) is Material, 'Can only add materials of type Material'        
        self.__materials.append(material)
    

class NewInventory(object):
    '''
    '''
    
    def __init__(self):        
        self.__items = []
    
    # privates
    def __get_items(self): return tuple(self.__items)
    
    # properties
    items = property(__get_items, None, None, 'Read-only collection of items that are stored in this Inventory.')    
    
    # methods
    def add_item(self, item):
        assert type(item) is NewItem, 'Can only add items of type Item'
        self.__items.append(item)
        
class ItemNameGenerator(object):
    '''
    '''
    def __init__(self, template, materials):
        if not isinstance(template, Template) or not isinstance(materials, list):
             raise TypeError, "First parameter must be of type Template and second parameter must be a list of Materials"
        
        self.template = template
        self.materials = materials
        self.used_materials = []
        
    def generate_name(self):
        return ' '.join((self.getPrimary(), self.getSecondary(), self.template.name))
    
    def getPrimary(self):
        primary = self.template.primary_type
        for mat in self.materials:
            if mat not in self.used_materials and primary in mat.can_be:
                self.used_materials.append(mat)
                return '-'.join((mat.name, self.makePastTense(primary)))    
        return 'Unknown-typed'
    
    def getSecondary(self):
        secondary = self.template.secondary_type
        for mat in self.materials:
            if mat not in self.used_materials and secondary in mat.can_be:
                self.used_materials.append(mat)
                return mat.name
        return 'Unknown'
        
    def makePastTense(self, word):
        return word + 'd' if word.endswith('e') else word + 'ed'