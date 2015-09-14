from characters import Actor
from dataset import DatasetBuilder
from modes import PlayMode, EditMode
from pygame.locals import *
from scene import Scene
from utils import DebugPrint
import configuration
import gui
import os
import pygame
import sys
import time

LoadDefaultMap = False

class Effects(object):
    "All engine effects, like screen fades, lightning, etc."
    
    def __init__(self, engine):
        self.engine = engine
        self.currentEffect = Effects.NoEffect()
        
    def update(self, ticks):
        self.currentEffect.update(ticks)
        
    def render(self, surface):
        self.currentEffect.render(surface)
    
    def lightning(self, time):
        self.currentEffect = self.Lightning(self, time)
        
    def fade(self, time, fadeOut=True, color=(0,0,0)):
        self.currentEffect = self.Fade(self, time, fadeOut, color)
    
    class NoEffect:
        def update(self, ticks): pass
        def render(self, surface): pass
        
    class Lightning:
        def __init__(self, effects, time):
            self.effects = effects
            self.time = time
            self.dt = self.effects.engine.clock.get_fps() / time * 255.0
            self.buffer = pygame.Surface(pygame.display.get_surface().get_size()).convert()
            self.buffer.fill((255,255,255))
            self.alpha = 200.0
            self.buffer.set_alpha(self.alpha)
            self.step = 0
            
        def update(self, ticks):
            "advance the lightning effect one frame"
            self.alpha -= self.dt
            if self.alpha <= 0.0:
                self.effects.currentEffect = Effects.NoEffect()
                
            self.buffer.set_alpha(self.alpha)
            self.step += 1
        
        def render(self, surface):
            "render what the lightning currently looks like"
            surface.blit(self.buffer, (0,0))
            if self.step > 5: self.buffer.fill((0,0,0))
        
    class Fade:
        def __init__(self, effects, time, fadeOut, color):
            self.effects = effects
            self.time = time
            self.fadeOut = fadeOut
            self.color = color
            self.fadeSurface = pygame.Surface(pygame.display.get_surface().get_size()).convert()
            self.fadeSurface.fill(self.color)
            self.old, self.cur = 0,0
            if self.fadeOut:
                self.alpha = 0.0                
            else:
                self.alpha = 255.0
            
        def update(self, ticks):
            self.fadeSurface.set_alpha(self.alpha)
            self.old = self.cur
            self.cur = ticks
            if self.fadeOut:                
                self.alpha += 255.0 * (float(self.cur - self.old) / float(self.time))
                if self.alpha >= 255.0:
                    self.effects.currentEffect = Effects.NoEffect()
            else:
                self.alpha -= 255.0 * (float(self.cur - self.old) / float(self.time))
                if self.alpha <= 0.0:
                    self.effects.currentEffect = Effects.NoEffect()
                    
        def render(self, surface):
            surface.blit(self.fadeSurface, (0,0))
    
    def fader(self, time, fadeOut=True, color=(0,0,0)):
        scr = pygame.display.get_surface()
        fadeSurface = pygame.Surface(scr.get_size()).convert()
        fadeSurface.fill(color)
        old = 0
        cur = 0
        alpha = 0.0
        old = pygame.time.get_ticks()
        cur = old
        if fadeOut:
            alpha = 0.0
            fadeSurface.set_alpha(alpha)
            while alpha < 255.0:
                self.engine.render()
                scr.blit(self.engine.buffer, (0,0))
                fadeSurface.set_alpha(alpha)
                scr.blit(fadeSurface, (0,0))
                old = cur
                cur = pygame.time.get_ticks()
                pygame.display.flip()
                alpha += 255. * (float(cur - old) / float(time))
        else:
            alpha = 255.0
            fadeSurface.set_alpha(alpha)
            while alpha > 0.0:
                self.engine.render()
                scr.blit(self.engine.buffer, (0,0))
                fadeSurface.set_alpha(alpha)
                scr.blit(fadeSurface, (0,0))
                old = cur
                cur = pygame.time.get_ticks()
                pygame.display.flip()
                alpha -= 255. * (float(cur - old) / float(time))

class Console(object):
    "An interactive python prompt from within Overworld."
    
    class StdoutCapture:
        """Small utility class for capturing the output of console commands
        and displaying them in the response buffer instead of on stdout.
        """
        
        def __init__(self, console):
            """Keeps a reference to the console handy."""
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._console = console
            
        def write(self, inp):
            """Writes to the console's response buffer."""
            wraps = len(inp)/80
            if wraps>0:
                for i in range(wraps):
                    inp = inp[:i*80] + '\n' + inp[i*80:]
            strs = inp.splitlines()
            strs.reverse()
            for i in strs:
                self._console._responseBuf.insert(0, i)
    
    def __init__(self, engine):        
        self.engine = engine
        w, h = pygame.display.get_surface().get_size()
        self._buffer = pygame.Surface((w, h/2)).convert_alpha()
        self._buffer.set_alpha(150)
        self.bgcolor = (0,0,0,150)
        self.fgcolor = (200,200,200,255)
        self._font = pygame.font.Font(None, 24)
        self.setPrompt("> ")
        self._inputBuf = ""
        self._historyBuf = []
        self._responseBuf = []
        self._locals = {'scene': self.engine.scene, 'console': self, 'engine': self.engine, 'effects' : self.engine.effects,
                        'play': self.engine.modes["play"], 'edit': self.engine.modes["edit"], 's': TestingSetup(self.engine.scene)}
        self._globals = {'quit': self.shutdownEngine }
        self.done = False
        
    def __del__(self):
        sys.stdout = sys.__stdout__
        
    def shutdownEngine(self):
        self.engine.done = True
        self.done = True
        
    def setPrompt(self, ps):
        self.promptStr = ps
        self._prompt = self._font.render(self.promptStr, 1, self.fgcolor)
        
    def update(self):
        # clean up the response buffer:
        self._responseBuf = [i.strip() for i in self._responseBuf]
        self._responseBuf = [i for i in self._responseBuf if i != '']
        if len(self._responseBuf) > 8: self._responseBuf = self._responseBuf[0:8]
            
    def render(self, surface):
        self.engine.scene.render(surface)
        
        self._buffer.fill(self.bgcolor)
        pygame.draw.line(self._buffer, (200,200,200,255), (0,self._buffer.get_height()-2), (self._buffer.get_width(), self._buffer.get_height()-2),2)

        # prompt:
        self._buffer.blit(self._prompt, (10,10))
        # input:
        self._input = self._font.render(self._inputBuf, 1, self.fgcolor)
        self._buffer.blit(self._input, (20 + self._prompt.get_width(), 10))
        # response:
        c = 0
        for i in self._responseBuf:
            try:
                response = self._font.render(i, 1, self.fgcolor)
                y = (c+1)*response.get_height()+20
                self._buffer.blit(response, (10, y))
                c += 1
            except pygame.error:
                self._responseBuf.insert(0, '**Error: too much text to display')

        surface.blit(self._buffer, (0,0))
    
    def handleInput(self, event):
        if event.type == KEYDOWN:

            if event.key == K_ESCAPE:
                self.done = True
                pygame.event.clear(KEYDOWN)
            
            elif event.key == K_RETURN:
                self.parseInput()

            elif event.key == K_SPACE:
                self._inputBuf += ' '            

            elif event.key == K_BACKSPACE:
                self._inputBuf = self._inputBuf[0:-1]

            elif event.key == K_UP:
                if len(self._historyBuf) == 0: return
                self._history += 1
                if self._history > len(self._historyBuf):
                    self._inputBuf = self._historyBuf[-1]
                    self._history = len(self._historyBuf)
                    return
                self._inputBuf = self._historyBuf[self._history-1]

            elif event.key == K_DOWN:
                if len(self._historyBuf) == 0: return
                self._history -= 1
                if self._history < 1:
                    self._inputBuf = ""
                    self._history = 0
                    return
                self._inputBuf = self._historyBuf[self._history-1]

            else:
                tmpbuf = ""
                key = event.key

                if key >= K_a and key <= K_z:
                    if event.mod & KMOD_SHIFT:
                        key -= 32
                    tmpbuf += chr(key)
                elif key >= K_EXCLAIM and key < K_a:        
                    tmpbuf += event.unicode

                if tmpbuf != '':
                    self._inputBuf += tmpbuf
                    
    def parseInput(self):
        if self._inputBuf == "": return
        try:
            co = compile(self._inputBuf, "<oworld>", "single")
            exec co in self._globals, self._locals
        except Exception, message:
            self._responseBuf.insert(0, '**Error: %s' % message)

        self._historyBuf.insert(0, self._inputBuf)
        self._history = 0
        self._inputBuf = ""
        
    def run(self):
        oldstdout = sys.stdout
        sys.stdout = self.StdoutCapture(self)
        surface = pygame.display.get_surface()
        self.done = False
        while not self.done:
            self.update()
            for e in pygame.event.get():
                self.handleInput(e)
                
            self.render(surface)
            
            pygame.display.flip()

        sys.stdout = oldstdout

class Engine(object):
    
    def __init__(self):
        print "Hijacking stdout...",
        self._hijackStdout()
        sys.__stdout__.write("done\n\n")
        
        print "Initializing Pygame"
        self._initPygame()
        print "Finished Pygame Initialization\n"

        pd = gui.ProgressDialog("Initializing Overworld...")
        pd.start()
                
        print "Initializing Data\n"
        self._initData(pd)
        print "Finished Data Initialization\n"
        
        print "Initializing Game"
        self._initGame(pd)
        print "Finished Game Initialization\n"
        
        pd.end()
        
    def _hijackStdout(self):
        sys.stdout = DebugPrint()
        
    def _initData(self, progressDialog=None):
        """This method looks in the "data" directory for new or modified data files that ought
        to be incorporated into datasets. See the Overworld documentation for details on 
        organizing datasets.
        """
        
        print "Building Spritesets"
        self._buildSpritesets()
        progressDialog.updateProgress(20)
        print "Finished Building Spritesets\n"
        
        print "Building Tilesets"
        self._buildTilesets()
        progressDialog.updateProgress(20)
        print "Finished Building Tilesets\n"
        
        print "Building Scripts"
        self._buildScripts()
        progressDialog.updateProgress(20)
        print "Finished Building Scripts\n"
        
        print "Building Dialogs"
        self._buildDialogs()
        progressDialog.updateProgress(20)
        print "Finished Building Dialogs\n"

        print "Building Items"
        self._buildItems()
        progressDialog.updateProgress(20)
        print "Finished Building Items"
        
    def _initPygame(self):        
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(configuration.screen_resolution, HWSURFACE|DOUBLEBUF)
        self.buffer = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        pygame.display.set_caption("Overworld %s-alpha" % time.strftime("%Y.%m.%d"))
        
    def _initGame(self, progressDialog=None):
        self.holding_shift = False
        
        if LoadDefaultMap and os.path.exists(os.path.join(configuration.mapdir, 'default.map')):
            self.scene = Scene.load(os.path.join(configuration.mapdir, 'default.map'), self, progressDialog=progressDialog)
        else:
            self.scene = Scene(self, drawGrid=False, borderUnwalkable=True, borderTrigger=True, progressDialog=progressDialog)
            
        self.scene.initScene()
        
        self.modes = {"edit": EditMode(self), "play": PlayMode(self)}
        self.mode = self.modes["edit"]
        self.effects = Effects(self)      
        self.done = False
        
        if progressDialog: progressDialog.updateProgress(10)
    
    def handleInput(self): self.mode.handleInput()

    def update(self):
        dx, dy = 0, 0
        
        if self.holding_shift: self.scene.setPartySpeed(10)
        else: self.scene.setPartySpeed(2)
        
        if self.movingRight: dx = 1
        if self.movingLeft: dx = -1
        if self.movingUp: dy = -1
        if self.movingDown: dy = 1
            
        self.scene.moveParty(dx,dy)
        self.scene.centerAt(self.scene.player.px, self.scene.player.py)
        t = self.clock.tick(30) # throttled to 30 fps
        self.scene.update(t) 
        self.effects.update(t)
        
    def render(self):
        self.scene.render(self.buffer)
        self.effects.render(self.buffer)
            
    def renderText(self):
        fpsTxt1 = self.font.render("FPS: %.2f" % self.clock.get_fps(), True, (200,200,200))
        self.buffer.blit(fpsTxt1, (10,10))
    
    def run(self):

        welcomeMessage = """
Welcome to Overworld!

To use the latest test script, open the console and type: s.setup()

The test script will run and you will be able to try out the functionality it sets up.
"""
        gui.Dialog.createOkDialog(welcomeMessage).run()

        while not self.done:        
            self.handleInput()
            self.update()
            self.render()
            self.mode.render(self.buffer)
            self.renderText()
            self.screen.blit(self.buffer, (0,0))
            pygame.display.flip()
            
    def quit(self):
        print "Quitting..."
        self.done = True
            
    def warpPlayerToTile(self, tx, ty):
        self.scene.player.px = tx * self.scene.tileFactory.tileWidth
        self.scene.player.py = ty * self.scene.tileFactory.tileHeight
        self.scene.centerAt(self.scene.player.px, self.scene.player.py)        
                                           
    def _buildSpritesets(self):
        DatasetBuilder().buildDataset(configuration.spritesetdir)
                
    def _buildTilesets(self):
        DatasetBuilder().buildDataset(configuration.tilesetdir)
    
    def _buildScripts(self):
        DatasetBuilder().buildDataset(configuration.scriptdir)
        
    def _buildDialogs(self):
        DatasetBuilder().buildDataset(configuration.dialogdir)
        
    def _buildItems(self):
        DatasetBuilder().buildDataset(configuration.itemdir)
    
class TestingSetup(object):
    
    def __init__(self, scene):
        self.scene = scene
        
    def setup(self):
        shopkeeper = Actor(self.scene, "sentry")
        shopkeeper.name = "HK-47"
        shopkeeper.dialogId = "shopkeeper"
        
        for i in range(5):
            flashlight = self.scene.itemCollector.createItem(shopkeeper, "Flashlight")
            shopkeeper.inventory.stowItem(flashlight)

        for i in range(5):
            staff = self.scene.itemCollector.createItem(shopkeeper, "Staff")
            shopkeeper.inventory.stowItem(staff)
            
        self.scene.addActorToScene(shopkeeper)

        print "Created shopkeeper named %s with 5 flashlights and 5 staves and moved him to (200,200)" % shopkeeper.name
        
        shopkeeper.moveTo((200,200))
        
        self.scene.player.inventory.stowItem(self.scene.itemCollector.createItem(self.scene.player, "Staff"))
        self.scene.player.inventory.stowItem(self.scene.itemCollector.createItem(self.scene.player, "Staff"))
        self.scene.player.inventory.stowItem(self.scene.itemCollector.createItem(self.scene.player, "Flashlight"))
        self.scene.player.inventory.stowItem(self.scene.itemCollector.createItem(self.scene.player, "Flashlight"))
        
        print "Created 2 staves and 2 flashlights and added them to player's inventory"
