import pygame
import configuration
import constants
import os
import items
import types
import gui
from cStringIO import StringIO
from zipfile import ZipFile

class DialogCollector(object):
    """This class reads the appropriate data directories for actor dialogs. It then stores them by id
    (based on the directory name) for reference by npc actors.
    """
    
    def __init__(self, scene, dialogset):
        self.scene = scene
        self.dialogset = dialogset
        self.dialogs = {}
        self.otherFuncs = []
        self._loadDialogset()
        
    def splitSets(self, namelist):
        sets = {}
        for name in namelist:
            set, item = tuple(os.path.split(os.path.split(name)[0]))
            if not set in sets: sets[set] = {}
            if not item in sets[set]: sets[set][item] = []
            sets[set][item].append(name)
        return sets
        
    def _loadDialogset(self):       
        """Read the "dialogs" data directory for zip files that contain         
        dialog.py files. Incorporate that into the collection of dialogs.
        """
        
        z = ZipFile(configuration.dialogs)
        dialogs = self.splitSets(z.namelist())
        
        for dialog in dialogs:
            for id in dialogs[dialog]:
                for dialog_file in dialogs[dialog][id]:
                    dialog_script = z.read(dialog_file)
                    speakFunc, otherFuncs = self.getFunctions(z, dialog_file)
                    self.dialogs[id] = speakFunc
                    self.otherFuncs += otherFuncs
            
    def getFunctions(self, zipFile, dialog):
        dialogStr = zipFile.read(dialog)        
        # clean up the script
        dialogStr = dialogStr.replace('\r', '') 
        if not dialogStr.endswith('\n'): dialogStr += "\n"
        otherFuncs = []
        speakFunc = None
        locals = {'scene': self.scene, 'engine': self.scene.engine, 'gui': gui}
        globals = {}        
        exec(dialogStr,locals,globals)
        for glbl in globals:
            if type(globals[glbl]) == types.FunctionType:
                if glbl == "speak": speakFunc = globals[glbl]
                else: otherFuncs.append(globals[glbl])
            
        return speakFunc, otherFuncs
    
    def runDialog(self, actor):
        class otherFuncs: pass
        for i in self.otherFuncs: setattr(otherFuncs, i.__name__, staticmethod(i))
        self.dialogs[actor.dialogId](otherFuncs, actor, self.scene)
        
class ItemCollector(object):
    "Handles the loading and instancing of items."
    
    def __init__(self, scene, itemset):
        self.scene = scene
        self.itemset = itemset
        self.items = {}
        self.itemDescriptions = {}
        self._loadItems()
        
    def splitSets(self, namelist):
        sets = {}
        for name in namelist:
            set, item = tuple(os.path.split(os.path.split(name)[0]))
            if not set in sets: sets[set] = {}
            if not item in sets[set]: sets[set][item] = []
            sets[set][item].append(name)
        return sets
        
    def _loadItems(self):
        "Read the itemset zip file for item zips, creating Item objects along the way."
        print "loading itemset: %s" % self.itemset
        z = ZipFile(configuration.items)
        itemsets = self.splitSets(z.namelist())
        
        for itemset in itemsets[self.itemset]:
            item_filenames = itemsets[self.itemset][itemset]
            item = items.Item(None, self)
            for item_filename in item_filenames:
                if item_filename.endswith('.py'): 
                    script = z.read(item_filename)
                    self._setItemData(item, script)
                elif item_filename.endswith('.png'):
                    item.image = pygame.image.load(StringIO(z.read(item_filename))).convert_alpha()                
                else:
                    print 'Skipping unknown filetype "%s"' % item_filename
                    continue
                    
            print "Created item: %s" % item.name
            self.items[item.name] = item
        
        z.close()
                
    def _setItemData(self, item, script):
        # clean up the script 
        script = script.replace('\r', '') 
        if not script.endswith('\n'): script = script+"\n"

        l = {'EquipTypes': constants.EquipTypes, 'JobTypes': constants.JobTypes, 'EquipLocation': constants.EquipLocation}
        g = {}        
        exec(script,l,g)
        for t in g:
            i = t.lower()
            if type(g[t]) == types.FunctionType: item.events[t] = g[t]
            elif i == "name": item.name = g[t]
            elif i == "value": item.fullValue = g[t]
            elif i == "equip_type" or i.startswith('type') or i == "equiptype": item.types = g[t]
            elif i.startswith('equip_loc') or i.startswith('loc'): item.locations = g[t]
            elif i == "jobs" or i == "jobtype" or i == "job" : item.jobs = g[t]
            elif i == "attack": item.attack = g[t]
            elif i == "attack_bonus" or i == "attackbonus": item.attackBonus = g[t]
            elif i == "defense": item.defense = g[t]
            elif i == "defense_bonus" or i == "defensebonus": item.defenseBonus = g[t]
            elif i == "description" or i == "desc": self.itemDescriptions[item.name] = g[t]
            else: print "Skipping %s: %s" % (type(g[t]), i)
                        
    def createItem(self, character, itemName):
        """Creates a new copy of the specified item by replicating the "master" version created
        when the item files were loaded"""
        
        if itemName not in self.items: 
            raise Exception, "Invalid item name"
        if not character.inventory or not isinstance(character.inventory, items.Inventory): 
            raise Exception, "Must pass a valid inventory"
            
        ret = items.Item(character.inventory, self)
        orig = self.items[itemName]
        for attr in orig.__dict__.keys():
            ret.__setattr__(attr, orig.__dict__[attr])
        ret.inventory = character.inventory
            
        return ret
    
    def getDescription(self, itemName):
        """Gets the singular instance of an item's description.  No need to duplicate
        big strings unnecessarily"""
        
        if itemName in self.itemDescriptions: return self.itemDescriptions[itemName]
        else: return None
