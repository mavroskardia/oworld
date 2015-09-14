# subscreens.py
# Classes that display game data to the user (or editor)
# by Andrew Martin (2006)
#
# TODO:
#    [] Comment all classes
#    [] Rename members that don't adhere to style guidelines
#    [] Review algorithms to determine if there is a more pythonic way
#    [] Review classes included in module for relevance to module
#

from characters import Spriteset
from gui import *
from items import *
from pygame.locals import *
from zipfile import ZipFile
import configuration
import constants
import os
import pygame
import sys
import threading

class Subscreen(Application):
    """Constructs and manages the GUI for all subscreen actions."""
                
    def __init__(self, scene, **kwargs):
        Application.__init__(self, **kwargs)
        self.scene = scene
        self.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (0,0,0,0)
        self._initComponents()
        
    def __repr__(self): return "Subscreen"
    
    def _initComponents(self):
        listbox = ListBox(parent=self, width=self.width-40, height=self.height-40, pos=(15,20))
        self.add(listbox)
        
        for pc in self.scene.players:
            control = CharacterListControl(pc)
            control.width = listbox.width-5
            listbox.add(control)
        
        closeButton = Button(borderWidth=2, text="X", font=pygame.font.Font(None, 15), callback=lambda x,y: self.exit())
        closeButton.width = closeButton.height
        closeButton.x = self.x+self.width-closeButton.width-3
        closeButton.y = self.y+2
        
        self.add(closeButton)

    def keypress(self, event):
        if event.key == K_ESCAPE: self.exit()
        if event.key == K_TAB: self.exit()

class ItemDisplay(BorderedControl):
    
    def __init__(self, item, depreciate=False, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        self.item = item
        if depreciate: self.item.cost = int(self.item.cost * self.item.depreciationFactor)
        self._initComponents()
        
    def _initComponents(self):
        fc = (0,0,0)
        
        # Item Image
        image = Image(parent=self, surface=self.item.image, width=50, height=50, borderWidth=2)        
        # Item Name
        name = Label(parent=self, text=self.item.name, fontColor=fc)        
        # Item Count (if greater than 1)
        self.count = Label(parent=self, text="Count: %d" % self.item.count if self.item.count > 0 else "", fontColor=fc)        
        # Item Cost
        cost = Label(parent=self, text="Cost: %d" % self.item.cost, fontColor=fc)
        
        # position the controls

        image.x, image.y = 10, 10

        name.x = image.right + 5
        name.y = image.y+(image.height-name.height)/2
        
        self.count.x = image.x
        self.count.y = image.bottom + 5
        
        cost.x = self.count.x
        cost.y = self.count.bottom + 5
        
        self.add(image); self.add(name); self.add(self.count)
        self.add(cost)

class CharacterListControl(Button):
    """Wrap all player data to be displayed in a single control for the big listbox."""
            
    def __init__(self, character, **kwargs):            
        Button.__init__(self, **kwargs)
        self._character = character
        self.backgroundColor = (0,0,0,0)
        self.borderWidth = 0
        self._initControls()
        self.callback = self.showCharacterScreen
        
    def showCharacterScreen(self, event, control):
        CharacterScreen(self._character).run()
        
    def _initControls(self):
        
        self.children = []
        # 6 distinct child controls
        
        # Sprite picture
        spriteImage = Image(parent=self, surface=self._character._spriteset[2][0], pos=(5, 5))
        self.add(spriteImage)
        
        # Name label
        nameLabel = Label(text=self._character.name, parent=self)
        nameLabel.x = spriteImage.x+spriteImage.width+10
        nameLabel.y = spriteImage.y
        nameLabel.width = 200
        self.add(nameLabel)
                
        # Level label
        levelLabel = Label(text="Level: %d" % self._character.level, parent=self)
        levelLabel.x = nameLabel.x + nameLabel.width
        levelLabel.y = nameLabel.y
        self.add(levelLabel)
        
        # HP Label
        hpLabel = Label(text="%d/%d HP" % (self._character.hp, self._character.maxHp), parent=self)
        hpLabel.x = nameLabel.x
        hpLabel.y = nameLabel.y + nameLabel.height
        hpLabel.width = 200
        self.add(hpLabel)
        
        # AP Label
        apLabel = Label(text="%d/%d AP" % (self._character.ap, self._character.maxAp), parent=self)
        apLabel.x = hpLabel.x + hpLabel.width
        apLabel.y = hpLabel.y
        self.add(apLabel)
        
        # Experience bar
        expPb = ProgressBar(width=200, height=16, borderWidth=2)
        expPb.x = hpLabel.x
        expPb.y = spriteImage.y+spriteImage.height - expPb.height
        expPb.min = self._character.levelExpStart
        expPb.max = self._character.levelExpEnd
        expPb.value = self._character.experience
        self.add(expPb)
                    
        self.height = spriteImage.height + 10
        
    def __repr__(self): return "CharacterControl"
             
class InventoryControl(BorderedControl):
    """Display a character's inventory in graphical form and has support for
    drag and drop.
    """
    
    def __init__(self, character, **kwargs):
        BorderedControl.__init__(self, **kwargs)

        if "grid_line_color" in kwargs: self.gridLineColor = kwargs["grid_line_color"]
        else: self.gridLineColor = (50,50,50)
        
        self.character = character
        self.width = 32*10
        self.height = 32*10
        
    def __repr__(self): return "InventoryControl"
        
    def _renderGrid(self, surface):
        xspaces, yspaces = self.width / 32, self.height / 32

        for x in xrange(1, xspaces): 
            pygame.draw.line(surface, self.gridLineColor, (self.x+x*32, self.y+self.borderWidth), (self.x+x*32, self.y+self.height-self.borderWidth))

        for y in xrange(1, yspaces):
            pygame.draw.line(surface, self.gridLineColor, (self.x+self.borderWidth, self.y+y*32), (self.x+self.width-self.borderWidth-1, self.y+y*32))
        
    def render(self, surface):        
        BorderedControl.flatRender(self, surface)
        self._renderGrid(surface)
        
    def mouseEnter(self, event):
        for c in self.children:
            if isinstance(c, InventoryItemControl): c.mouseOver = False
        for c in self.getControlsAt(event.pos):
            if isinstance(c, InventoryItemControl): c.mouseOver = True
            
    def mouseLeave(self, event):
        for c in self.children:
            if isinstance(c, InventoryItemControl): c.mouseOver = False
            
    def supressOtherChildren(self, favoredChild):
        for c in self.children:
            if c != favoredChild: c.itemBubble.forceHide()    
         
class OldInventoryControl(BorderedControl):
    "Display a character's inventory in graphical form"
    
    def __init__(self, character, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        
        if "grid_line_color" in kwargs: self.gridLineColor = kwargs["grid_line_color"]
        else: self.gridLineColor = (50,50,50) # really dark gray
        
        self.character = character
        self.width = 32*10
        self.height = 32*10

    def orderItems(self):
        dx, dy = 0, 0
        for item in self.character.inventory.stowed:
            itm = InventoryItemControl(item, item.count, parent=self, pos=(dx,dy))
            dx += item.width*32
            if dx > self.width: dx, dy = 0, dy + item.height * 32

            print "Adding InventoryItemControl at (%d,%d)" % (itm.x, itm.y)
            self.add(itm)
            
    def __repr__(self): return "InventoryControl"
        
    def _renderGrid(self, surface):
        xspaces, yspaces = self.width / 32, self.height / 32

        for x in xrange(1, xspaces): 
            pygame.draw.line(surface, self.gridLineColor, (self.x+x*32, self.y+self.borderWidth), (self.x+x*32, self.y+self.height-self.borderWidth))

        for y in xrange(1, yspaces):
            pygame.draw.line(surface, self.gridLineColor, (self.x+self.borderWidth, self.y+y*32), (self.x+self.width-self.borderWidth-1, self.y+y*32))
        
    def render(self, surface):        
        BorderedControl.flatRender(self, surface)
        self._renderGrid(surface)
        
    def mouseEnter(self, event):
        for c in self.children:
            if isinstance(c, InventoryItemControl): c.mouseOver = False
        for c in self.getControlsAt(event.pos):
            if isinstance(c, InventoryItemControl): c.mouseOver = True
            
    def mouseLeave(self, event):
        for c in self.children:
            if isinstance(c, InventoryItemControl): c.mouseOver = False
            
    def supressOtherChildren(self, favoredChild):
        for c in self.children:
            if c != favoredChild: c.itemBubble.forceHide()

class InventoryItemControl(BorderedControl):
    "Item in the inventory grid"

    def __init__(self, item, count, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        
        self.item = item
        self.width = 32 * item.width
        self.height = 32 * item.height
        self.count = count
        self.font = pygame.font.Font(None, 15)
        self._initItemBubble()
        self.mouseOver = False
        self.popupDelay = 5
        
    def __repr__(self): return "InventoryItemControl"            

    def __get_mo(self): return self.__mouse_over
    def __set_mo(self, mo): self.__mouse_over = mo        
    def __del_mo(self): del self.__mouse_over
    mouseOver = property(__get_mo, __set_mo, __del_mo, "Mouse is over this control")

    def _renderCountText(self, surface):
        txt = self.font.render("%d" % self.count, True, (100,100,100))
        surface.blit(txt, (self.x+self.width-txt.get_width(), self.y+self.height-txt.get_height()+2))
        
    def render(self, surface):
        surface.blit(self.item.image, (self.x, self.y))
        
        if self.mouseOver:
            self.popupDelay = 5
            self.itemBubble.show = True
            self.parent.supressOtherChildren(self)
        else:
            self._renderCountText(surface)
            self.popupDelay -= 1
            if self.popupDelay == 0:
                self.popupDelay = 5
                self.itemBubble.hideUnlessActive()
            
        Control.render(self, surface)
            
    def mouseEnter(self, event):
        BorderedControl.mouseEnter(self, event)
        self.mouseOver = True
        
    def mouseLeave(self, event):
        BorderedControl.mouseLeave(self, event)
        self.mouseOver = False
            
    def mouseDown(self, event):
        BorderedControl.mouseDown(self, event)
        print "Mouse down on %s" % self.item.name

class ItemBubble(DialogBubble):

    def __init__(self, item, **kwargs):
        DialogBubble.__init__(self, **kwargs)
        self.item = item        

        if 'showPrice' in kwargs: self.showPrice = kwargs['showPrice']
        else: self.showPrice = False
        if 'showEquip' in kwargs: self.showEquip = kwargs['showEquip']
        else: self.showEquip = True
        if 'showDrop' in kwargs: self.showDrop = kwargs['showDrop']
        else: self.showDrop = True
        if 'showBuy' in kwargs: self.showBuy = kwargs['showBuy']
        else: self.showBuy = False
        if 'showSell' in kwargs: self.showSell = kwargs['showSell']
        else: self.showSell = False

        if 'backgroundColor' not in kwargs: self.backgroundColor = (180,220,245)
        if 'borderColor' not in kwargs: self.borderColor = (0,0,0)

        self._initComponents()
        
    def __repr__(self): return "ItemBubble"
        
    def _initComponents(self):
        f = pygame.font.Font(None, 20)
        
        img = Image(surface=self.item.image, parent=self, pos=(10,10), borderWidth=0)
        self.add(img)
        
        name = Label(text=self.item.name, font=f)
        name.x = img.x + img.width + 5
        name.y = 10
        self.add(name)
        
        if self.item.count > 1:
            count = Label(text="Count: %d" % self.item.count, parent=self, font=f)
            count.x = name.x
            count.y = name.bottom
            self.add(count)

        if self.showDrop and self.item.count > 1:
            dropAll = Button(text="Drop All", parent=self, borderWidth=2)
            dropAll.x = self.width - self.spoutSize - dropAll.width - 10
            dropAll.y = self.height - dropAll.height - 10
            self.add(dropAll)
            
            dropButton = Button(text="Drop", parent=self, borderWidth=2, callback=self.dropButtonCb)
            dropButton.x = dropAll.x - self.spoutSize - dropButton.width - 10
            dropButton.y = dropAll.y
            self.add(dropButton)
            
        elif self.showDrop:
            dropButton = Button(text="Drop", parent=self, borderWidth=2, callback=self.dropButtonCb)
            dropButton.x = self.width - self.spoutSize - dropButton.width - 10
            dropButton.y = self.height - dropButton.height - 10
            self.add(dropButton)            
            
        if self.showEquip and self.item.locations != constants.EquipLocation.Not_Equippable:
            # add an "equip" button
            equipButton = Button(text="Equip", borderWidth=2)
            equipButton.x = 10
            equipButton.y = self.height - equipButton.height - 10
            self.add(equipButton)
            
        if self.showBuy:
            buyButton = Button(text="Buy", borderWidth=2, callback=self.buyButtonCb)
            buyButton.x = 10
            buyButton.y = self.height - buyButton.height - 10
            self.add(buyButton)
        elif self.showSell:
            sellButton = Button(text="Sell", borderWidth=2, callback=self.sellButtonCb)
            sellButton.x = 10
            sellButton.y = self.height - sellButton.height - 10
            self.add(sellButton)
        
        locStrList = constants.EquipLocation.attributeList(self.item.locations)        
        locStr = ",".join(locStrList)
        locStr = locStr.replace('_', ' ')
        equipType = Label(text=locStr, parent=self, font=f)
        if self.item.count > 1:
            equipType.x = count.x
            equipType.y = count.bottom
        else:
            equipType.x = name.x
            equipType.y = name.bottom
        self.add(equipType)
        
        desc = MultilineLabel(parent=self, font=f, borderWidth=1, backgroundColor=(255,255,255), borderColor=(170,150,120))
        desc.width = self.width - self.spoutSize - 20
        if self.showDrop: desc.height = self.height - img.height - dropButton.height - 30
        elif self.showBuy: desc.height = self.height - img.height - buyButton.height - 30
        elif self.showSell: desc.height = self.height - img.height - sellButton.height - 30
        else: desc.height = self.height - img.height - 30        
        desc.text = self.item.description
        desc.x = 10
        desc.y = img.y + img.height + 5
        self.add(desc)        
                
        self.show = False
        self.renderOnTop = True
        self.inMotion = False
            
    def dropButtonCb(self, event, button):
        self.item.drop()
        print "Clicked drop button on item: %s" % self.item.name
#        for iic in self.ancestor.inventory._children:
#            iibc = iic._children[0]
#            if iibc.item == self.item:
#                if iic.item.count == 0:
#                    self.ancestor.inventory.remove(iic)
#                    self.ancestor.remove(iic)
#                    self.ancestor.resetInventory()
#                    self.show = False
#                           
#                break
            
    def buyButtonCb(self, event, button):
        print "Buying %s for %s" % (self.item.name, self.item.cost)

    def sellButtonCb(self, event, button):
        print "Selling %s for %s" % (self.item.name, self.item.cost)
        
    def mouseEnter(self, mousePos):
        DialogBubble.mouseEnter(self, mousePos)
        self.inMotion = True
        
    def mouseLeave(self, mousePos):
        DialogBubble.mouseLeave(self, mousePos)
        self.inMotion = False
        self.show = False
        
    def mouseMotion(self, mousePos):
        DialogBubble.mouseMotion(self, mousePos)
        self.inMotion = True

    def forceHide(self): 
        self.show = False
        self.inMotion = False
        
    def hideUnlessActive(self):
        if not self.inMotion: self.show = False
        
class StatsDisplay(BorderedControl):
    
    def __init__(self, character, **kwargs):
        BorderedControl.__init__(self, **kwargs)        

        self.backgroundColor = 'backgroundColor' in kwargs and kwargs['backgroundColor'] or (255,255,255)
        
        if "editable" in kwargs: self.editable = kwargs["editable"]
        else: self.editable = False
        
        self.character = character
        self.font = pygame.font.Font(None, 22)
        
        self._initComponents()
        
        print "width/height: %d/%d" % (self.width, self.height)
        
    def __repr__(self): return "Stats Display"
        
    def _initComponents(self):
        self.children = []
        # Stats Labels
        self.statLabels = {}
        dy = 5
        max_width = 200
        for stat in self.character.stats.keys():
            statLabel = Label(text="%s:" % stat, parent=self, width=80, fontColor=(0,0,0))
            statLabel.x = 10
            statLabel.y = dy
            max_width = max(statLabel.width, max_width)
            self.add(statLabel)
            dy += statLabel.height

            for substat in self.character.stats[stat].keys():
                substatLabel = Label(text="%s" % substat, parent=self, width=120, font=self.font, fontColor=(0x99, 0x99, 0x99))
                substatLabel.x = statLabel.x + 10
                substatLabel.y = dy
                substatLabel.clicked = self.statClicked
                substatValue = Label(text="%s" % self.character.stats[stat][substat], parent=self, width=50, xalignment="right", font=self.font, fontColor=(0x99,0x99,0x99))
                substatValue.x = substatLabel.x + substatLabel.width
                substatValue.y = substatLabel.y
                max_width = max(max_width, substatLabel.width+substatValue.width+50)
                self.add(substatLabel)
                self.add(substatValue)
                self.statLabels[substatLabel] = substatValue
                dy += substatValue.height
                
            dy += 10
                
        self.width = max_width
        if dy > self.height: self.height = dy
        
    def statClicked(self, event, control):
        if self.editable:
            id = InputDialog("Enter new value for %s:" % control.text)
            id.run()
            if id.result: 
                try: 
                    self.character.stats.setSubstatValue(control.text, int(id.textInput.text))
                    self.statLabels[control].text = id.textInput.text
                except Exception, e: print 'Could not set %s to "%s" (%s)' % (control.text, id.textInput.text, e)
        
class CharacterScreen(Application):
    """Shows a character's attributes, vitals, statistics, inventory, etc.
    and optionally allows editing of those values.
    """
    
    def __init__(self, character, **kwargs):
        Application.__init__(self, **kwargs)
        
        self.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (0,0,0,0)
        self.editable = kwargs['editable'] if "editable" in kwargs else False
        self.character = character
        self.initControls()

    def initControls(self):
        "Create and add all controls to the app."
        fnt = pygame.font.Font(configuration.monofont, 15)
        fnt.set_bold(True)

        self.border = BorderedControl(parent=self, pos=(20,30), width=self.width-40, height=self.height-40)
        self.border.borderWidth = 2
                    
        self.closeButton = Button(text="X", callback=self.exit, borderWidth=2, parent=self, font=pygame.font.Font(None, 15))
        self.closeButton.width = self.closeButton.height
        self.closeButton.x = self.width-self.closeButton.width-3
        self.closeButton.y = self.y+2
        self.add(self.closeButton)

        # Sprite picture
        self.spriteImage = Image(parent=self.border, surface=self.character._spriteset[2][0], pos=(10,10))
        if self.editable: self.spriteImage.clicked = self.spritesetChangeCb
        self.border.add(self.spriteImage)
        
        # Name label
        self.nameLabel = Label(text=self.character.name, parent=self.border, font=fnt)
        self.nameLabel.x = self.spriteImage.right + 10
        self.nameLabel.y = self.spriteImage.y
        self.nameLabel.width = 200
        if self.editable: self.nameLabel.clicked = self.nameChangeCb
        self.border.add(self.nameLabel)
        
        # Job Label
        if not self.character.job: jobtxt = "Jobless"
        else: jobtxt = repr(self.character.job)
        f = pygame.font.Font(configuration.regfont, 15)
        f.set_italic(True)
        f.set_bold(True)
        self.jobLabel = Label(text=jobtxt, parent=self.border, font=f)
        self.jobLabel.x = self.nameLabel.right + 10
        self.jobLabel.y = self.nameLabel.y
        self.border.add(self.jobLabel)
        
        # Level label
        self.levelLabel = Label(text="Level %d" % self.character.level, parent=self.border, font=fnt)
        self.levelLabel.x = self.nameLabel.x
        self.levelLabel.y = self.nameLabel.bottom
        if self.editable: self.levelLabel.clicked = self.levelChangeCb
        self.border.add(self.levelLabel)
        
        # HP Label
        self.hpLabel = HpCurMaxLabel(self.character, parent=self.border, font=fnt)
        self.hpLabel.x = self.spriteImage.right + 10
        self.hpLabel.y = self.levelLabel.y + self.levelLabel.height
        self.border.add(self.hpLabel)

        # AP Label
        self.apLabel = ApCurMaxLabel(self.character, parent=self.border, font=fnt)
        self.apLabel.x = self.hpLabel.x
        self.apLabel.y = self.hpLabel.y + self.hpLabel.height 
        self.border.add(self.apLabel)
        
        # Inventory display
        self.inventory = ListBox(parent=self.border, width=300, height=300, borderWidth=2, backgroundColor=(255,255,255))
        self.inventory.x = self.border.width - self.inventory.width - 10
        self.inventory.y = self.border.height - self.inventory.height - 10
        #self.inventory.orderItems()
        for item in self.character.inventory.stowed: 
            self.inventory.add(ItemListControl(item, parent=self.inventory))
        self.border.add(self.inventory)

        # Player stats
        self.stats = StatsDisplay(self.character, parent=self.border, editable=self.editable, borderWidth=2)
        self.stats.x = 10
        self.stats.y = self.inventory.y
        self.stats.height = self.inventory.height
        self.border.add(self.stats)
        
        if self.editable: self._initEditableComponents()
        
        self.add(self.border)
        
    def _initEditableComponents(self):
        # position
        self.positionLabel = Label(text="Position: (%d,%d)" % (self.character.px, self.character.py), parent=self.border, font=pygame.font.Font(configuration.regfont, 12))
        self.positionLabel.x = self.spriteImage.x
        self.positionLabel.y = self.spriteImage.bottom + 5
        self.positionLabel.clicked = self.changePositionCb        
        self.border.add(self.positionLabel)
        
        # 'accept' button        
        self.okButton = Button(text="OK", parent=self, callback=self.exit, borderWidth=2, font=pygame.font.Font(None, 15))
        self.okButton.height = self.closeButton.height
        self.okButton.x = self.closeButton.x - self.okButton.width - 5
        self.okButton.y = self.closeButton.y
        self.add(self.okButton)
        
        # dialog set choice
        self.dialogsetLabel = Label(text="Dialog ID: %s" % self.character.dialogId, parent=self.border, font=pygame.font.Font(configuration.regfont, 12))
        self.dialogsetLabel.x = self.positionLabel.x
        self.dialogsetLabel.y = self.positionLabel.bottom + 5
        self.dialogsetLabel.clicked = self.dialogsetChangeCb
        self.border.add(self.dialogsetLabel)
        
        # add inventory item
        self.addItemButton = Button(text="Add Item", parent=self.border, callback=self.listItemsCb, pos=(self.inventory.x, self.inventory.bottom))
        self.border.add(self.addItemButton)
        
    def keypress(self, event):
        if event.key == K_ESCAPE: self.exit()
        if event.key == K_TAB: self.exit()

    def listItemsCb(self, event, control):
        controls = []
        for item in self.character.scene.itemCollector.items.keys():
            controls.append(Button(text=item, callback=self.addItemCb))
            
        ControlDialog("Choose item:", controls).run()  
        
    def addItemCb(self, event, control):
        item = self.character.scene.itemCollector.createItem(self.character, control.text)
        self.character.inventory.stowItem(item)
        print "Added %s to %s's inventory" % (item.name, self.character.name)
        
    def resetInventory(self):
        self.inventory.sort()
        for iic in self.inventory.children: iic.itemBubble = None
        
    def dialogsetChangeCb(self, event, control):
        controls = []
        for dialogId in self.character.scene.dialogCollector.dialogs.keys():
            controls.append(Button(text=dialogId, callback=self.dialogsetChoiceCb))
        ControlDialog("Choose dialog:", controls).run()
    
    def dialogsetChoiceCb(self, event, control):
        self.character.dialogId = control.text
        self.dialogsetLabel.text = "Dialog ID: %s" % self.character.dialogId
        control.ancestor.exit()
        
    def levelChangeCb(self, event, control):
        id = InputDialog("Enter new value for level:")
        id.run()
        if id.result:
            try:
                val = int(id.textInput.text.split('.')[0])
                self.character.level = val
                self.levelLabel.text = "Level %d" % self.character.level
                self.stats._initComponents()
            except Exception, e:
                ErrorDialog("Failed to set level. (%s)" % e).run()
        
    def statChangeCb(self, event, stat):
        id = InputDialog("Enter new value for \"%s\":" % stat)
        id.run()
        if id.result:
            try:
                val = int(id.textInput.text)
                self.character.stats[stat] = val
                self.statLabels[stat].text = "%s: %d" % (stat, self.character.stats[stat])
            except Exception, e:
                ErrorDialog("Failed to set new stat. (%s)" % e).run()
                    
    def changePositionCb(self, event, button):
        id = InputDialog("Enter new position in pixels (max: %d,%d)" % (self.character.scene.widthInPixels, self.character.scene.heightInPixels))
        id.run()
        if id.result: 
            try:
                new_pos = id.textInput.text.replace('(', '')
                new_pos = new_pos.replace(')', '')
                x = int(new_pos.split(',')[0].strip())
                y = int(new_pos.split(',')[1].strip())
                self.character.px = x
                self.character.py = y
                self.positionLabel.text = "Position: (%d,%d)" % (self.character.px, self.character.py)
                print "New position: (%d,%d)" % (self.character.px, self.character.py)
            except Exception, e:
                ErrorDialog("Could not read new position value. (%s)" % e).run()
    
    def spriteChoiceCb(self, event, button):
        try:
            #ssfn = os.path.join(configuration.spritesetdir, button.text+".zip")
            #print "Opening spriteset at %s" % ssfn
            ss = Spriteset(button.text)
            self.character.changeSpriteset(ss)
            self.spriteImage.surface = self.character._spriteset[Spriteset.SOUTH][0]
            self.nameLabel.x = self.spriteImage.right + 10
            self.jobLabel.x = self.nameLabel.right + 10
            self.apLabel.x = self.nameLabel.x
            self.hpLabel.x = self.nameLabel.x
            self.levelLabel.x = self.nameLabel.x
            button.ancestor.done = True
        except Exception, ex:
            ErrorDialog(text="Failed to read spriteset at that location! (%s)" % ex).run()

    def spritesetChangeCb(self, event, button):
        controls = []
        z = ZipFile(configuration.spritesets)
        for spriteset in dataset.splitSets(z.namelist()):
            controls.append(Button(text=spriteset, callback=self.spriteChoiceCb))
        ControlDialog("Choose spriteset:", controls).run()
    
    def nameChangeCb(self, button, event):
        id = InputDialog(text="Enter new name:")
        id.run()
        self.character.name = id.textInput.text
        self.nameLabel.text = self.character.name

class ItemListControl(BorderedControl):
    """A custom control for displaying relevant information in the scrolling list box that
    is a character's inventory.
    """
    
    def __init__(self, item, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        self.borderWidth = 0
        self.backgroundColor = (0,0,0,0)
        
        if 'showPrice' in kwargs: self.showPrice = kwargs['showPrice']
        else: self.showPrice = False
        
        if 'showEquip' in kwargs: self.showEquip = kwargs['showEquip']
        else: self.showEquip = True
        
        if 'showDrop' in kwargs: self.showDrop = kwargs['showDrop']
        else: self.showDrop = True
        
        if 'showBuy' in kwargs: self.showBuy = kwargs['showBuy']
        else: self.showBuy = False

        if 'showSell' in kwargs: self.showSell = kwargs['showSell']
        else: self.showSell = False

        self.item = item
        self._initComponents()
        
    def _initComponents(self):
        "Component layout is: Name ... [ @Price ] xCount"
                
        self.children = []
        if self.showPrice and self.item.cost > self.item.owner.money: self.cannotBuy = True
        else: self.cannotBuy = False
        
        if self.cannotBuy: self.nameLabel = Label(text=self.item.name, parent=self, fontColor=(200,0,0))
        else: self.nameLabel = Label(text=self.item.name, parent=self)
            
        self.add(self.nameLabel)
        
        if self.showPrice: 
            if self.cannotBuy: self.countLabel = Label(text="@%d x%d" % (self.item.cost, self.item.count), parent=self, fontColor=(200,0,0))
            else: self.countLabel = Label(text="@%d x%d" % (self.item.cost, self.item.count), parent=self)
        else: self.countLabel = Label(text="x%d" % self.item.count, parent=self)
            
        if self.parent: self.width = self.parent.width - 20
        else: self.width = self.nameLabel.width + self.countLabel.width

        self.height = self.nameLabel.height

        self.countLabel.x = self.width - self.countLabel.width - 10 
        self.add(self.countLabel)
        
        self.itemBubble = None
        
    def __repr__(self): return "ItemListControl"
        
    def mouseEnter(self, event):
        if not self.itemBubble: 
            self.itemBubble = ItemBubble(self.item, width=250, height=200, borderWidth=2, 
                                         spoutX=self.absx, spoutY=self.absy+self.height/2,
                                         cornerRadius=15, showEquip=self.showEquip, showDrop=self.showDrop, 
                                         showSell=self.showSell, showBuy=self.showBuy and not self.cannotBuy)
            self.ancestor.add(self.itemBubble)
            
        self.itemBubble.show = True
        
    def mouseLeave(self, event):
        threading.Thread(target=self.hideItemBubble).start()
        
    def hideItemBubble(self):
        threading._sleep(0.3) # not sure what a good timeout would be
        self.itemBubble.hideUnlessActive()

class HpCurMaxLabel(BorderedControl):
    
    def __init__(self, character, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        self.borderWidth = 0
        self.backgroundColor = (0,0,0,0)
        if "font" in kwargs: self.font = kwargs["font"]
        else: self.font = pygame.font.Font(None, 20)
        self.character = character
        self.amountLabel = Label(text="%d/%d" % (self.character.hp, self.character.maxHp), width=100, parent=self, font=self.font)
        self.add(self.amountLabel)
        self.width = self.amountLabel.width + 30
        self.typeLabel = Label(text="HP", parent=self, pos=(self.width-20,0), width=20, xalignment="right", font=self.font)
        self.add(self.typeLabel)
        self.height = self.typeLabel.height
        
    def render(self, surface):        
        self.amountLabel.text = "%d/%d" % (self.character.hp, self.character.maxHp)
        Control.render(self, surface)
        
class ApCurMaxLabel(BorderedControl):
    
    def __init__(self, character, **kwargs):
        BorderedControl.__init__(self, **kwargs)
        self.borderWidth = 0
        self.backgroundColor = (0,0,0,0)
        if "font" in kwargs: self.font = kwargs["font"]
        else: self.font = pygame.font.Font(None, 20)
        self.character = character
        self.amountLabel = Label(text="%d/%d" % (self.character.ap, self.character.maxAp), width=100, parent=self, font=self.font)
        self.add(self.amountLabel)
        self.width = self.amountLabel.width + 30
        self.typeLabel = Label(text="AP", parent=self, pos=(self.width-20,0), width=20, xalignment="right", font=self.font)
        self.add(self.typeLabel)
        self.height = self.typeLabel.height
        
    def render(self, surface):        
        self.amountLabel.text = "%d/%d" % (self.character.ap, self.character.maxAp)
        Control.render(self, surface)
