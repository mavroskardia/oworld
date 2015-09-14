# tiles.py
# All classes related to the organization and display of tiles.
# author: Andrew Martin (2006)
#
# TODO:
#    [] Comment all classes
#    [] Rename members that don't adhere to style guidelines
#    [] Review algorithms to determine if there is a more pythonic way
#    [] Review classes invluded in module for relevance to module
#

from cStringIO import StringIO
from pygame.locals import *
from zipfile import ZipFile
import configuration
import dataset
import gui
import imageutil
import os
import pygame
import xml.dom.minidom

class TileSelector(object):
    
    def __init__(self, scene):
        self.scene = scene
        self.app = gui.Application(backgroundColor=(200,200,200))
        self.app.keypress = self._appKeypressCb
        self.selectedTile = 0
        self._initComponents()
        
    def _initComponents(self):
        # determine how many tiles there are to display:
        numTilesPerRow = self.scene.viewport.widthInPixels / self.scene.tileFactory.tileWidth - 3 # leave enough room on the end
        numTilesPerCol = self.scene.viewport.heightInPixels / self.scene.tileFactory.tileHeight - 2
        
        px, py = 2, 2
        xc, yc = 0, 0
        leftovers = []
        
        for t in xrange(0, len(self.scene.tileFactory)):
            
            tileImg = self.scene.tileFactory.tiles[t]
            button = gui.ImageButton(parent=self.app, pos=(px,py), image=tileImg, width=tileImg.get_width(), height=tileImg.get_width())
            button.borderWidth = 0
            button.backgroundColor = (0,0,0,0)
            button.tileIndex = t
            button.callback = self._tileClickedCb
            self.app.add(button)
            xc += 1
            px += self.scene.tileFactory.tileWidth + 2 # a little padding between tiles
            if xc >= numTilesPerRow:
                xc = 0
                yc += 1
                px = 2
                py += self.scene.tileFactory.tileHeight + 2
            
        px, py = 0, py+self.scene.tileFactory.tileHeight + 2
        for it in self.scene.tileFactory.irregularTiles.keys():
            tileImg = self.scene.tileFactory.irregularTiles[it][0]
            button = gui.ImageButton(parent=self.app, pos=(px,py), image=tileImg, width=tileImg.get_width(), height=tileImg.get_height())
            button.borderWidth = 0
            button.backgroundColor = (0,0,0,0)
            button.tileName = it
            button.callback = self._irregularClickedCb
            self.app.add(button)
            px += tileImg.get_width()
                
        closeButton = gui.Button(text="X", callback=self._closeButtonCb, backgroundColor=(0,0,0,100))
        closeButton.x = self.app.width - closeButton.width
        closeButton.y = 0
        self.app.add(closeButton)
    
    def _closeButtonCb(self, event, button):
        self.app.done = True
    
    def _tileClickedCb(self, event, tileControl):
        self.selectedTile = tileControl.tileIndex
        self.app.done = True

    def _irregularClickedCb(self, event, tileControl):
        self.selectedTile = tileControl.tileName
        self.app.done = True
    
    def _appKeypressCb(self, event):
        if event.key == K_TAB or event.key == K_ESCAPE: self.app.done = True
    
    def show(self):
        self.app.done = False
        self.app.run()   
        
class TileFactory(object):
    """Loads a zip file full of tiles and stores them for Tile objects to reference."""
    
    def __init__(self, tileset, tileWidth, tileHeight):
        self.tileset = tileset
        self.tileWidth = tileWidth
        self.tileHeight = tileHeight
        self.specialTiles = {}
        self.irregularTiles = {}
        self.tiles = self.readTilesetFile()
                
    def readTilesetFile(self):
        ret = []
        z = ZipFile(configuration.tilesets)
        nl = z.namelist()
        
        tilesets = dataset.splitSets(nl)
                
        for name in tilesets[self.tileset]:
            data = z.read(name)
            pbuf = StringIO(data)
            origSprite = pygame.image.load(pbuf).convert_alpha()
            
            if name.endswith('base.png'): 
                base = origSprite # special case "default" tile
                continue
            elif name.endswith('generic_container.png'): 
                gc = origSprite
                continue
            
            size = origSprite.get_size()
            if size[0] > self.tileWidth or size[1] > self.tileHeight:
                print "Splitting image \"%s\" into tiles..." % name
                sprites = imageutil.convertToTiles(origSprite, self.tileWidth, self.tileHeight)
                print "Done splitting"
                tileName = os.path.split(name)[-1]
                print "cataloging irregular tile %s" % tileName
                self.irregularTiles[tileName] = (origSprite, sprites)
            else: 
                sprites = [origSprite]
    
                for sprite in sprites:
                    b1 = imageutil.createHorizontalBlendedAlphaMask(sprite, 0.2, 1.0)
                    b2 = imageutil.createHorizontalBlendedAlphaMask(sprite, 0.8, 0.0)
                    b3 = imageutil.createVerticalBlendedAlphaMask(sprite, 0.2, 1.0)
                    b4 = imageutil.createVerticalBlendedAlphaMask(sprite, 0.8, 0.0)            
                    ret.append(sprite)
                    
                    if b1: ret.append(b1)
                    if b2: ret.append(b2)
                    if b3: ret.append(b3)
                    if b4: ret.append(b4)
            
        z.close()
        if base: 
            ret.append(base)
            self.specialTiles['base'] = ret.index(base)
        if gc: 
            ret.append(gc)
            self.specialTiles['generic_container'] = ret.index(gc)
        
        return ret
        
    def __len__(self): return len(self.tiles)

class Tile(object):
    
    def __init__(self, tileFactory, tileIndex):
        self.tileIndex = tileIndex
        self.tileFactory = tileFactory
        
    def render(self, surface, x, y):
        try: surface.blit(self.tileFactory.tiles[self.tileIndex], (x,y))
        except Exception: pass 
            #print "Unable to render tile with index: %s" % self.tileIndex
            
class IrregularTile(Tile):
    def __init__(self, tileFactory, tileName, tileIndex):
        self.tileName = tileName
        self.tileIndex = tileIndex
        self.tileFactory = tileFactory
        
    def render(self, surface, x, y):
        surface.blit(self.tileFactory.irregularTiles[self.tileName][1][self.tileIndex], (x,y))
    
class Tilestack(object):
    """A vertical stack of tiles in two parts: those rendered below the actors and those rendered
    above.
    """
    
    def __init__(self):
        self.baseTiles = []
        self.roofTiles = []
        self.isWalkable = True
        self.triggerId = None
        self.contents = None
        
    def __len__(self): return len(self.baseTiles) + len(self.roofTiles)
        
    def renderBase(self, surface, x, y):
        """Render only the base tiles."""
        for t in self.baseTiles: t.render(surface, x, y)
            
    def renderRoof(self, surface, x, y):
        """Render only the roof tiles."""
        for t in self.roofTiles: t.render(surface, x, y)

    def addBaseTile(self, tile):
        """Add the specified tile to the base portion of the stack."""
        if len(self.baseTiles) == 0: self.baseTiles.append(tile)
        elif self.baseTiles[-1].tileIndex != tile.tileIndex: self.baseTiles.append(tile)
        
    def addRoofTile(self, tile):
        """Add the specified tile to the roof portion of the stack."""
        if len(self.roofTiles) == 0: self.roofTiles.append(tile)
        elif self.roofTiles[-1].tileIndex != tile.tileIndex: self.roofTiles.append(tile)              
        
    def removeTopBaseTile(self):
        """Removes the topmost tile in the base stack. If there is only
        one tile remaining, does nothing.
        """
        if len(self.baseTiles)>1: self.baseTiles = self.baseTiles[:-1]
            
    def removeTopRoofTile(self):
        """Removes the topmost tile in the roof stack. The roof stack
        can potentially be empty.
        """
        self.roofTiles = self.roofTiles[:-1]
        
    def performAction(self, scene):
        scene.actionObject = self
        scene.scriptRunner.execute(self.triggerId)
        scene.actionObject = None
        
    def toXml(self):
        ret = xml.dom.minidom.Element("tilestack")
        ret.attributes["walkable"] = "%s" % self.isWalkable
        ret.attributes["trigger"] = "%s" % self.triggerId
        
        baseXml = xml.dom.minidom.Element("base")
        for t in self.baseTiles:
            bxml = xml.dom.minidom.Element("tile")
            bxml.attributes["index"] = "%s" % t.tileIndex
            if isinstance(t, IrregularTile):
                bxml.attributes["name"] = "%s" % t.tileName
            baseXml.appendChild(bxml)
        ret.appendChild(baseXml)
        
        roofXml = xml.dom.minidom.Element("roof")
        for t in self.roofTiles:
            rxml = xml.dom.minidom.Element("tile")
            rxml.attributes["index"] = "%s" % t.tileIndex
            if isinstance(t, IrregularTile):
                rxml.attributes["name"] = "%s" % t.tileName
            roofXml.appendChild(rxml)
        ret.appendChild(roofXml)
        return ret
    
    def fromXml(tsXml, tileFactory):
        ret = Tilestack()
        
        if tsXml.attributes["walkable"].value == "False": ret.isWalkable = False
        else: ret.isWalkable = True
        
        if tsXml.attributes["trigger"].value == "None": ret.triggerId = None
        else: ret.triggerId = tsXml.attributes["trigger"].value
        
        baseXml = tsXml.getElementsByTagName("base")[0]
        for tileXml in baseXml.getElementsByTagName("tile"):
            tileIndex = int(tileXml.attributes["index"].value)
            if tileXml.hasAttribute('name'):
                tileName = tileXml.attributes['name'].value
                ret.baseTiles.append(IrregularTile(tileFactory, tileName, tileIndex))
            else:
                ret.baseTiles.append(Tile(tileFactory, tileIndex))
            
        roofXml = tsXml.getElementsByTagName("roof")[0]
        for tileXml in roofXml.getElementsByTagName("tile"):
            tileIndex = int(tileXml.attributes["index"].value)
            if tileXml.hasAttribute('name'):
                tileName = tileXml.attributes['name'].value
                ret.roofTiles.append(IrregularTile(tileFactory, tileName, tileIndex))
            else:
                ret.roofTiles.append(Tile(tileFactory, tileIndex))
                
        return ret
    
    fromXml = staticmethod(fromXml)
