from math import ceil
from pygame.locals import *
import engine
import gui
import pygame
import scene
import subscreens
import tiles

class PlayMode(object):
    "Input functionality for play mode defined here."
    
    def __init__(self, engine): self.engine = engine
    def __repr__(self): return "Play Mode"
    
    def addItemCb(self, event, control):
        fl = self.engine.scene.itemCollector.createItem(self.engine.scene.player, control.text)
        self.engine.scene.player.inventory.stowItem(fl)
        print "Added %s to player inventory" % fl.name
    
    def handleInput(self):

        events = pygame.event.get()        
        for e in events:
            if e.type == KEYDOWN:
                
                if e.key == K_ESCAPE: self.showMenu()
               
                elif e.key == K_i:
                    gui.ControlDialog("Choose item:", [gui.Button(text=item, callback=self.addItemCb) for item in self.engine.scene.itemCollector.items.keys()]).run()
                    
                elif e.key == K_m:
                    self.engine.mode = self.engine.modes["edit"]
                    
                elif e.key == K_TAB:
                    subscreens.Subscreen(self.engine.scene).run()
                                        
                elif e.key == K_BACKQUOTE:
                    console = engine.Console(self.engine)
                    console.run()
                    
                elif e.key == K_SPACE:
                    # perform the "main" action: initiate dialog, open chests, etc.
                    self.engine.scene.performPlayerAction()
                    
                elif e.key == K_F1:
                    help = """
`: show console
TAB: show party screen
m: switch to edit mode
i: add an item to player inventory
ESC: quit Overworld"""

                    gui.Dialog(help).run()
                
            elif e.type == QUIT:
                self.engine.done = True
        
        keys = pygame.key.get_pressed()
        self.engine.movingRight = keys[K_RIGHT]
        self.engine.movingLeft = keys[K_LEFT]
        self.engine.movingUp = keys[K_UP]
        self.engine.movingDown = keys[K_DOWN]        
        self.engine.holding_shift = pygame.key.get_mods() & KMOD_SHIFT
        
    def render(self, surface):
        "Play mode needs no special rendering"
        pygame.mouse.set_visible(True)
        
    def showMenu(self):        
        "Displays the options available while in edit mode."
        def quitButtonCb(event, button):
            button.ancestor.done = True
            self.engine.quit()
        def switchToEditModeCb(event, button):
            self.engine.mode = self.engine.modes['edit']
            button.ancestor.done = True
            
        editModeButton = gui.Button(text="Edit Mode", callback=switchToEditModeCb)
        quitButton = gui.Button(text="Quit", callback=quitButtonCb)
        controls = [editModeButton, quitButton]
        cd = gui.ControlDialog("Play Mode", controls, width=300)
        cd.run()
    
class EditMode(object):

    def __init__(self, engine):
        self.engine = engine
        self.layerInUse = "base"
        self.middleClickAction = "walk"
        self.walkPaintMode = False
        self.pressingLeftButton = False
        self.pressingMiddleButton = False
        self.pressingRightButton = False
        self.selectedTile = 0
        self.selectMode = False
        self.sceneDirty = False
        
    def __repr__(self): return "Edit Mode"
    
    def __get_scene(self): return self.engine.scene
    scene = property(__get_scene, None, None, "Retrieves the engine's scene object")
    
    def __get_tf(self): return self.engine.scene.tileFactory
    tileFactory = property(__get_tf, None, None, "Retrieves the engine's scene's tile factory")
    
    def handleInput(self):
        
        events = pygame.event.get()        
        for e in events:
            if e.type == KEYDOWN:
                
                if e.key == K_ESCAPE: 
                    self.showMenu()
                elif e.key == K_m:
                    self.engine.mode = self.engine.modes["play"]
                elif e.key == K_r:
                    old = self.layerInUse
                    if old == "base": self.layerInUse = "roof"
                    else: self.layerInUse = "base"                        
                    print "Changing layer from %s to %s" % (old, self.layerInUse)
                elif e.key == K_s:
                    self.selectMode = not self.selectMode
                elif e.key == K_t:
                    old = self.middleClickAction
                    if old == "walk": self.middleClickAction = "trigger"
                    else: self.middleClickAction = "walk"                    
                    print "Changing middle click from %s to %s" % (old, self.middleClickAction)
                elif e.key == K_w:
                    self.walkPaintMode = not self.walkPaintMode
                    print "Changing walk paint mode from %s to %s" % (not self.walkPaintMode, self.walkPaintMode)
                elif e.key == K_a:
                    npc = Actor(self.scene, "../data/spritesets/guy.zip")
                    subscreens.CharacterScreen(npc, editable=True).run()
                    self.scene.addActorToScene(npc)
                    self.sceneDirty = True
                elif e.key == K_p:
                    subscreens.CharacterScreen(self.scene.player, editable=True).run()
                elif e.key == K_n:
                    c = self.scene.createCharacter()                    
                    self.scene.addPlayerToParty(c)
                    self.sceneDirty = True
                elif e.key == K_TAB:
                    ts = tiles.TileSelector(self.scene)
                    ts.show()
                    self.selectedTile = ts.selectedTile 
                elif e.key == K_BACKQUOTE:
                    console = engine.Console(self.engine)
                    console.run()
                elif e.key == K_F1:
                    help = """
Help:
A: add new actor to scene
N: add new actor to party
TAB: show tile selector
`: show console
F1: this help
M: change to play mode
W: change walk painting mode
T: change to trigger painting mode
ESC: show edit mode menu
R: toggle base/roof tile painting modes
L: toggle showing base, roof, or base/roof
P: edit the main player character"""

                    d = gui.Dialog(help)
                    #d.textLabel.font = pygame.font.Font(configuration.monofont, 14)
                    d.run()
                                        
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 1: self.pressingLeftButton = True
                if e.button == 2: self.pressingMiddleButton = True
                if e.button == 3: self.pressingRightButton = True
                    
            elif e.type == MOUSEBUTTONUP:
                if e.button == 1: self.pressingLeftButton = False
                if e.button == 2: self.pressingMiddleButton = False
                if e.button == 3: self.pressingRightButton = False
                
            elif e.type == QUIT:
                self.engine.done = True
        
        keys = pygame.key.get_pressed()
        self.engine.movingRight = keys[K_RIGHT]
        self.engine.movingLeft = keys[K_LEFT]
        self.engine.movingUp = keys[K_UP]
        self.engine.movingDown = keys[K_DOWN]        
        self.engine.holding_shift = pygame.key.get_mods() & KMOD_SHIFT    
        
        if self.pressingLeftButton: self.handleLeftButton()
        else: self.selectionStartX, self.selectionStartY = -1, -1
        if self.pressingMiddleButton: self.handleMiddleButton()
        if self.pressingRightButton: self.handleRightButton()
        
    def handleLeftButton(self):
        self.sceneDirty = True
        mousePos = pygame.mouse.get_pos()
        if self.selectMode:
            if self.selectionStartX == -1: self.selectionStartX = mousePos[0]
            if self.selectionStartY == -1: self.selectionStartY = mousePos[1]
            
        else:
            ts = self.engine.scene.getTilestackAt(self.scene.viewport.x+mousePos[0], self.scene.viewport.y+mousePos[1])
            if self.layerInUse == "base":
                if isinstance(self.selectedTile, int):                
                    ts.addBaseTile(tiles.Tile(self.tileFactory, self.selectedTile))
                elif isinstance(self.selectedTile, str):
                    # an irregularly-sized tile, so paint it's pieces separately
                    self.paintIrregularTile(mousePos)
            else:
                ts.addRoofTile(tiles.Tile(self.tileFactory, self.selectedTile))

    def paintIrregularTile(self, mousePos, remove=False):
        itiles = self.tileFactory.irregularTiles[self.selectedTile][1]
        itw, ith = self.tileFactory.irregularTiles[self.selectedTile][0].get_size()
        rows = int(ceil(float(itw) / self.tileFactory.tileWidth))
        cols = int(ceil(float(ith) / self.tileFactory.tileHeight))
        
        px, py, i = 0, 0, 0
        roofRows = int(rows / 3) # one-third of rows should be roof, subscribing to the "2/3" view we are using
        for c in range(cols):
            for r in range(rows):
                ts = self.scene.getTilestackAt(self.scene.viewport.x+mousePos[0]+px, 
                                               self.scene.viewport.y+mousePos[1]+py)
                if c <= roofRows: 
                    if remove: ts.removeTopRoofTile()
                    else: ts.addRoofTile(tiles.IrregularTile(self.tileFactory, self.selectedTile, i))
                else: 
                    if remove: ts.removeTopBaseTile()
                    else: ts.addBaseTile(tiles.IrregularTile(self.tileFactory, self.selectedTile, i))
                px += self.tileFactory.tileWidth
                i += 1
            px = 0
            py += self.tileFactory.tileHeight
            
    def handleMiddleButton(self):
        self.sceneDirty = True
        mousePos = pygame.mouse.get_pos()
        ts = self.engine.scene.getTilestackAt(self.scene.viewport.x+mousePos[0], self.scene.viewport.y+mousePos[1])
        if self.middleClickAction == "walk": ts.isWalkable = self.walkPaintMode
        else:
            id = gui.InputDialog("Enter trigger ID:")
            id.run()
            print "Received trigger id: %s" % id.textInput.text
            if id.textInput.text and id.textInput.text != "":
                triggerId = id.textInput.text.replace(" ", "_")
                ts.triggerId = triggerId
            self.pressingMiddleButton = False
        
    def handleRightButton(self):
        self.sceneDirty = True
        mousePos = pygame.mouse.get_pos()        
        ts = self.scene.getTilestackAt(self.scene.viewport.x+mousePos[0], self.scene.viewport.y+mousePos[1])
        
        if type(self.selectedTile) is str:
            # remove the whole irregular tile from the current spot
            self.paintIrregularTile(mousePos, True)
        else:        
            if self.layerInUse == "base": ts.removeTopBaseTile()
            else: ts.removeTopRoofTile()
        self.pressingRightButton = False
        
    def render(self, surface):        
        "Edit mode special renderings"
        vx, vy = self.scene.viewport.x, self.scene.viewport.y
        x,y = pygame.mouse.get_pos()
        
        tmpSurface = pygame.Surface(surface.get_size()).convert_alpha()
        tmpSurface.fill((0,0,0,0))

        txtStart = tmpSurface.get_height()-70
        
        layerTxt = self.engine.font.render("Layer: %s" % self.layerInUse, True, (200,200,200))
        tmpSurface.blit(layerTxt, (10, txtStart))
        
        txtStart += 15        
        selectModeTxt = self.engine.font.render("Select mode: %s" % self.selectMode, True, (200,200,200))
        tmpSurface.blit(selectModeTxt, (10, txtStart))
        
        txtStart += 15        
        middleClickModeTxt = self.engine.font.render("Middle-click mode: %s" % self.middleClickAction, True, (200,200,200))
        tmpSurface.blit(middleClickModeTxt, (10, txtStart))
                
        if self.middleClickAction == "walk":
            txtStart += 15
            walkModeTxt = self.engine.font.render("Walk Paint Mode: %s" % self.walkPaintMode, True, (200,200,200))
            tmpSurface.blit(walkModeTxt, (10, txtStart))
        
        ts = self.scene.getTilestackAt(vx+x, vy+y)
        if ts.triggerId:
            txtStart += 15
            triggerTxt = self.engine.font.render("Trigger id: %s" % ts.triggerId, True, (200,200,200))
            tmpSurface.blit(triggerTxt, (10, txtStart))
            
        if self.selectMode:
            pygame.mouse.set_visible(True)
            if self.selectionStartX != -1 and self.selectionStartY != -1:
                pygame.draw.rect(tmpSurface, (0x55,0xee,0xff,50), (self.selectionStartX, self.selectionStartY, x-self.selectionStartX, y-self.selectionStartY))
                pygame.draw.rect(tmpSurface, (255,255,255,180), (self.selectionStartX, self.selectionStartY, x-self.selectionStartX, y-self.selectionStartY), 1)
        else:
            if isinstance(self.selectedTile, str):
                tileToPlace = self.tileFactory.irregularTiles[self.selectedTile][0]
                pygame.mouse.set_visible(False)
                tx, ty = (x/self.tileFactory.tileWidth)*self.tileFactory.tileWidth, (y/self.tileFactory.tileHeight)*self.tileFactory.tileHeight
                tmpSurface.blit(tileToPlace, (tx,ty))
                pygame.draw.rect(tmpSurface, (255,255,255,100), (tx,ty,tileToPlace.get_width(), tileToPlace.get_height()), 1)
            else: pygame.mouse.set_visible(True)
            
        surface.blit(tmpSurface, (0,0))
            
    def showMenu(self):        
        "Displays the options available while in edit mode."
        def saveScene(self):
            id = gui.InputDialog("Scene filename:", width=300)
            id.run()
            if id.result: self.scene.save(os.path.join(configuration.mapdir, id.textInput.text))
            self.sceneDirty = False
            cd.exit(None)
        def saveSceneButtonCb(button, event): saveScene(self)
        def loadSceneButtonCb(button, event):
            controls = []
            for file in [i for i in os.listdir(configuration.mapdir) if not i.startswith('.')]:
                controls.append(gui.Button(text=os.path.splitext(file)[0], callback=loadMapFileCb))
            lcd = gui.ControlDialog("Scene filename:", controls, width=300)
            lcd.run()
        def loadMapFileCb(event, button):
            scene = Scene.load(os.path.join(configuration.mapdir, button.text+'.map'), self.engine)
            if not scene: return
            self.engine.scene = scene
            self.engine.scene.initScene()
            button.ancestor.exit(None)
            cd.exit(None)
        def addCharacterButtonCb(button, event):
            c = self.scene.createCharacter()
            self.scene.actors.append(c)
            cd.exit(None)
        def quitButtonCb(event, button):
            button.ancestor.done = True
            self.engine.quit()
        def newSceneButtonCb(event, button):
            if self.sceneDirty:
                ynd = gui.Dialog.createYesNoDialog("Save existing scene first?")
                ynd.run()
                if ynd.result: saveScene(self)
            
            wid = gui.InputDialog("Enter new scene width")
            wid.run()
            w = int(wid.textInput.text) if wid.textInput.text.isdigit() else configuration.default_width_in_tiles
            
            hid = gui.InputDialog("Enter new scene height")
            hid.run()
            h = int(hid.textInput.text) if hid.textInput.text.isdigit() else configuration.default_height_in_tiles
            
            bid = gui.Dialog.createYesNoDialog("Choose different base tile?")
            bid.run()
            bt = None
            if bid.result:
                ts = TileSelector(self.scene)
                ts.show()
                bt = ts.selectedTile
                            
            self.engine.scene = scene.Scene(self.engine, widthInTiles=w, heightInTiles=h, players=[self.scene.player])
            if bt: self.engine.scene.baseTile = bt
            self.engine.scene.initScene()
            
            button.ancestor.exit()
            
        def switchToPlayModeCb(event, button):
            self.engine.mode = self.engine.modes["play"]
            button.ancestor.done = True
        
        playModeButton = gui.Button(text="Play Mode", callback=switchToPlayModeCb)
        newSceneButton = gui.Button(text="New Scene", callback=newSceneButtonCb)
        saveMapButton = gui.Button(text="Save Scene", callback=saveSceneButtonCb)
        loadMapButton = gui.Button(text="Load Scene", callback=loadSceneButtonCb)
        quitButton = gui.Button(text="Quit", callback=quitButtonCb)
        addCharacterButton = gui.Button(text="Add Character", callback=addCharacterButtonCb)
        controls = [playModeButton, newSceneButton, addCharacterButton, saveMapButton, loadMapButton, quitButton]
        cd = gui.ControlDialog("Edit Mode", controls, width=300)
        print "Control Dialog dimensions: %d x %d" % (cd.width, cd.height)
        print "Control Dialog position: (%d, %d)" % (cd.x, cd.y)
        cd.run()
