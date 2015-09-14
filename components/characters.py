# characters.py
# Classes related to the display of characters on the screen.
# by Andrew Martin (2006)
#
# TODO:
#    [x] Comment all classes
#    [x] Rename members that don't adhere to style guidelines
#    [x] Review algorithms to determine if there is a more pythonic way
#    [x] Review classes included in module for relevance to module
#

from cStringIO import StringIO
from items import Inventory
from random import randint
from zipfile import ZipFile
import configuration
import dataset
import os
import pygame

class Spriteset:
    """Spriteset takes care of the loading and organizing of individual frames of animation."""
    
    EAST, NORTH, SOUTH, WEST = 0,1,2,3
    
    def __init__(self, spriteset):
        self.__items = [[],[],[],[]]
        self.spriteset = spriteset
        z = ZipFile(configuration.spritesets)
        namelist = z.namelist()
        spritesets = dataset.splitSets(namelist)
        for s in spritesets[self.spriteset]:
            i = os.path.split(s)[-1]
            if i.startswith('e'): self.__items[Spriteset.EAST].append(pygame.image.load(StringIO(z.read(s))).convert_alpha())
            elif i.startswith('n'): self.__items[Spriteset.NORTH].append(pygame.image.load(StringIO(z.read(s))).convert_alpha())
            elif i.startswith('s'): self.__items[Spriteset.SOUTH].append(pygame.image.load(StringIO(z.read(s))).convert_alpha())
            elif i.startswith('w'): self.__items[Spriteset.WEST].append(pygame.image.load(StringIO(z.read(s))).convert_alpha())
            else: print 'Skipping invalid sprite file "%s"' % i
            
        z.close()

    def __repr__(self):
        return "East: %s\nNorth: %s\nSouth: %s\nWest: %s" % (self.__items[Spriteset.EAST], self.__items[Spriteset.NORTH], 
                                                             self.__items[Spriteset.SOUTH], self.__items[Spriteset.WEST])

    def __len__(self):
        len = 0
        for i in self.__items:
            for j in i: len += 1
        return len
    
    def __getitem__(self, key):
        if not key in (Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, Spriteset.WEST):
            raise KeyError, """key must be Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, or Spriteset.WEST"""
        else: return self.__items[key]
    
    def __setitem__(self, key, value):
        if not key in (Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, Spriteset.WEST):
            raise KeyError, """key must be Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, or Spriteset.WEST"""
        else: self.__items[key] = [value]

    def __delitem__(self, key):
        if not key in (Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, Spriteset.WEST):
            raise KeyError, """key must be Spriteset.EAST, Spriteset.NORTH, Spriteset.SOUTH, or Spriteset.WEST"""
        else: del self.__items[key]

    def __iter__(self): return self.__items.__iter__(self)

    def __contains__(self, item):
        for i in self.__items:
            for j in i: 
                if j == item: return True
        return False

    def getMaxWidth(self):
        """Return the width of the largest sprite in the set."""
        mx = 0
        for i in self.__items:
            for j in i: mx = max(mx, j.get_width()+2)
        return mx

    def getMaxHeight(self):
        """Return the height of the largest sprite in the set."""
        mx = 0
        for i in self.__items:
            for j in i: mx = max(mx, j.get_height()+2)
        return mx
    
class Sprite(object):
    """The Sprite class takes care of all the low-level animation functionality."""
    
    def __init__(self, spriteset, xoff=0, yoff=0, direction=Spriteset.EAST):
        object.__init__(self)
        
        if isinstance(spriteset, str): self._spriteset = Spriteset(spriteset)
        elif isinstance(spriteset, Spriteset): self._spriteset = spriteset
        
        # CAUTION: arbitrary magic numbers below!
        self._delay = 1000 / len(spriteset) # how many frames per second?
        self._stepx = pygame.display.get_surface().get_width() / 200
        self._stepy = pygame.display.get_surface().get_height() / 200

        self._autoMove = False
        self._movingLeft = False
        self._movingRight = False
        self._movingUp = False
        self._movingDown = False
        self._ticks = 0
        self._frame = 0
        self._tmpBuf = pygame.Surface((self._spriteset.getMaxWidth(), self._spriteset.getMaxHeight())).convert_alpha()
        self._updateRect = None
        self._should_update = True
        self.direction = direction
        self.px, self.py = 0, 0
        self.width, self.height = self._tmpBuf.get_size()
        self.image = self._spriteset[self.direction][self._frame]        
        self.update(1)        
        
    def getRect(self):
        """Returns the rect occupied by this sprite based on its current (px,py) and its width x height"""
        return (self.px, self.py, self.width, self.height)

    def update(self, tick):
        """Once per cycle, update the sprite.  If there has been enough delay since the last frame update,
        update the frame as well.
        """
        
        if self._autoMove: self.autoMove()
        else:
            if self._movingUp: self.moveUp(self._stepy)
            if self._movingDown: self.moveDown(self._stepy)
            if self._movingRight: self.moveRight(self._stepx)
            if self._movingLeft: self.moveLeft(self._stepx)

        self._ticks += tick
        if self._should_update:
            if self._ticks > self._delay:
                self._ticks = 0
                self._frame += 1
            
            if self._frame >= len(self._spriteset[self.direction]): self._frame = 0
            self.image = self._spriteset[self.direction][self._frame]
            self._should_update = False
                               
    def render(self, surf, pxoff=0, pyoff=0):
        "Renders the sprite to a surface with optional pixel offsets."        
        
        xoff = (self._tmpBuf.get_width() - self.image.get_width()) >> 1
        yoff = (self._tmpBuf.get_height() - self.image.get_height()) >> 1
        self._tmpBuf.blit(self.image, (xoff, yoff))
        surf.blit(self._tmpBuf, (self.px+pxoff, self.py+pyoff-self._tmpBuf.get_height()))        
        self._tmpBuf.fill((0,0,0,0))

    def setFrameNum(self, num):
        """Sets the currently rendered frame to the specified number"""
        if num >= len(self._spriteset[self.direction]) or num < 0: return
        self._frame = num
        self.image = self._spriteset[self.direction][self._frame]

    def getCurrentFrame(self): 
        """Returns the frame currently being rendered"""
        return self.image
    
    def getNumFrames(self): 
        """Returns the number of frames this sprite has for its current direction"""
        return len(self._spriteset[self.direction])

    def move(self, (dx,dy)):
        """Moves the sprite in the specified x and y directions. Takes care of updating
        frames and collision detection internally
        """
        
        if dx < 0: self.moveLeft(dx*-1)
        elif dx > 0: self.moveRight(dx)
        if dy < 0: self.moveUp(dy*-1)
        elif dy > 0: self.moveDown(dy)
        
    def autoMove(self):
        """With a desired location specified by the moveTo method, this method
        will incrementally move the sprite towards that position.
        """
        
        if self._destX < self.px: self.move((-self._stepx, 0))
        if self._destY < self.py: self.move((0, -self._stepy))
        if self._destX > self.px: self.move((self._stepx, 0))
        if self._destY > self.py: self.move((0, self._stepy))
        
        if self.isWithinStepRange((self._destX, self._destY)): self._autoMove = False
        
    def isWithinStepRange(self, dest):
        
        xInRange = self.px >= dest[0] - self._stepx and self.px <= dest[0] + self._stepx
        yInRange = self.py >= dest[1] - self._stepy and self.py <= dest[1] + self._stepy
        
        return xInRange and yInRange
    
    def moveTo(self, (x,y)):
        "Automatic movement to x,y through intermediate steps"
        
        self._autoMove = True
        self._destX, self._destY = x, y

    def moveLeft(self, dx):
        """Moves the sprite left or to the WEST direction"""
        
        self._should_update = True
        self._isMoving = True
        self.direction = Spriteset.WEST
        self.px -= dx
        
    def moveRight(self, dx):
        """Moves the sprite right or to the EAST direction"""
        
        self._should_update = True
        self._isMoving = True
        self.direction = Spriteset.EAST
        self.px += dx
        
    def moveUp(self, dy):
        """Moves the sprite up or to the NORTH direction"""
        
        self._should_update = True
        self._isMoving = True
        self.direction = Spriteset.NORTH
        self.py -= dy

    def moveDown(self, dy):
        """Moves the sprite down or to the SOUTH direction"""
        
        self._should_update = True
        self._isMoving = True
        self.direction = Spriteset.SOUTH
        self.py += dy

    def changeSpriteset(self, ss):
        """This method will keep all settings for the sprite, but change the spriteset
        to the newly specified one.
        """
    
        self._spriteset = ss
        self._tmpBuf = pygame.Surface((self._spriteset.getMaxWidth(), self._spriteset.getMaxHeight())).convert_alpha()
        self.width, self.height = self._tmpBuf.get_size()
        self._should_update = True
        self.update(self._delay+1)

class Actor(Sprite):
    """High level access to character's workings including name, stats,
    inventory, and whatever else we want to stick in the character.
    Subclass of the Sprite class to get all of the animation goodness
    for any actor in the game.
    """

    def __init__(self, scene, spriteset):
        Sprite.__init__(self, spriteset)
        self.scene = scene
        self.stats = ActorStats(self)
        self.name = "Chryso"
        self.job = None
        self.level = 1
        self.experience = 0
        self.maxHp = 10
        self.hp = 10
        self.maxAp = 5
        self.ap = 5
        self.money = 500
        self.inventory = Inventory(self)
        self.dialogId = "default"
        self.state = {}

    def __set_name(self, name): self.__name = name
    def __get_name(self): return self.__name    
    def __del_name(self): del self.__name        
    name = property(__get_name, __set_name, __del_name, "The actor's name")
    
    def __set_level_exp_start(self, level_exp_start): self.__level_exp_start = level_exp_start
    def __get_level_exp_start(self): return self.__level_exp_start    
    def __del_level_exp_start(self): del self.__level_exp_start        
    levelExpStart = property(__get_level_exp_start, __set_level_exp_start, __del_level_exp_start, "The actor's level_exp_start")
    
    def __set_level_exp_end(self, level_exp_end): self.__level_exp_end = level_exp_end
    def __get_level_exp_end(self): return self.__level_exp_end    
    def __del_level_exp_end(self): del self.__level_exp_end        
    levelExpEnd = property(__get_level_exp_end, __set_level_exp_end, __del_level_exp_end, "The actor's level_exp_end")
    
    def __get_job(self): return self.__job
    def __set_job(self, job): self.__job = job
    def __del_job(self): del self.__job
    job = property(__get_job, __set_job, __del_job, "The actor's current job")

    def __get_level(self): return self.__level
    def __set_level(self, lvl):
        if not hasattr(self, '__level'): self.__level = 0
        ol = self.__level        
        self.__level = lvl
        self.__level_exp_start, self.__level_exp_end = self._calculateLevelExp(lvl)
        self._calculateLevelStats(lvl-ol)        
    def __del_level(self): del self.__level
    level = property(__get_level, __set_level, __del_level, "The actor's level")
    
    def __get_experience(self): return self.__experience    
    def __set_experience(self, exp): self.__experience = exp        
    def __del_experience(self): del self.__experience
    experience = property(__get_experience, __set_experience, __del_experience, "The actor's experience")
    
    def __get_hp(self): return self.__hp
    def __set_hp(self, hp): self.__hp = hp
    def __del_hp(self): del self.__hp
    hp = property(__get_hp, __set_hp, __del_hp, "The actor's current hit points")
    
    def __get_max_hp(self): return self.__max_hp
    def __set_max_hp(self, maxhp): self.__max_hp = maxhp
    def __del_max_hp(self): del self.__max_hp
    maxHp = property(__get_max_hp, __set_max_hp, __del_max_hp, "The actor's max hit points")
    
    def __get_ap(self): return self.__ap
    def __set_ap(self, ap): self.__ap = ap
    def __del_ap(self): del self.__ap
    ap = property(__get_ap, __set_ap, __del_ap, "The actor's action points")
    
    def __get_max_ap(self): return self.__max_ap
    def __set_max_ap(self, maxap): self.__max_ap = maxap
    def __del_max_ap(self): del self.__max_ap
    maxAp = property(__get_max_ap, __set_max_ap, __del_max_ap, "The actor's max action points")
    
    def _calculateLevelExp(self, level):
        """Determines the range of experience for the specified level."""
        return (1000*(level-1), 1000*(level-1)+1000)
    
    def _calculateLevelStats(self, dl):
        """Determines new stat values for a level change (positive or negative)"""
        if dl > 0: multiplier = 1
        elif dl < 0: multiplier = -1
        else: multiplier = 0
        
        for i in range(dl): self.stats.updateStats(multiplier)
    
    def performDialog(self):
        """If the player tries to act on this actor, this will be called."""
        
        self.scene.dialogCollector.runDialog(self)
        
    def canBuyItem(self, item, payFullValue=True):
        return (item.fullValue if payFullValue else item.worth) < self.money
    
    def buyItem(self, seller, item, payFullValue=True):
        seller.money += item.fullValue if payFullValue else item.worth
        seller.inventory.removeItem(item)
        self.money -= item.fullValue if payFullValue else item.worth
        self.inventory.stowItem(item) 
        
class ActorStats(object):
    """A container class for the somewhat complicated stat layout for Overworld actors."""
    
    INT, CHAR, PHYS, SUPER = 0,1,2,3
    
    def __init__(self, character):
        self.actor = character
        self.Intelligence = {"Empathy":1, "Judgment":1, "Comprehension":1}
        self.Charisma = {"Attraction":1, "Leadership":1, "Influence":1}
        self.Physique = {"Endurance":1, "Speed":1, "Strength":1}
        self.Supernatural = {"Spirituality":1, "Dogma":1, "Piety":1}
        
    def keys(self): 
        """Returns the dict-like key list for iteration purposes"""
        
        return ["Intelligence", "Charisma", "Physique", "Supernatural"]
    
    def setSubstatValue(self, substatName, substatValue):
        """Sets the value for substatName without needing to know which stat that substat
        belongs to.
        """
        
        if substatName in self.Intelligence: self.Intelligence[substatName] = substatValue            
        elif substatName in self.Charisma: self.Charisma[substatName] = substatValue            
        elif substatName in self.Physique: self.Physique[substatName] = substatValue            
        elif substatName in self.Supernatural: self.Supernatural[substatName] = substatValue
        else: raise KeyError, "%s is not a valid substat" % substatName
    
    def __getitem__(self, index): return getattr(self, index)
    
    def updateStats(self, multiplier):
        """Modifies all stats by random values multiplied by the specified multiplier."""
        
        for stat in self.Intelligence.keys():
            self.Intelligence[stat] += (randint(0,5) * multiplier)
        for stat in self.Charisma.keys():
            self.Charisma[stat] += (randint(0,5) * multiplier)
        for stat in self.Physique.keys():
            self.Physique[stat] += (randint(0,5) * multiplier)
        for stat in self.Supernatural.keys():
            self.Supernatural[stat] += (randint(0,5) * multiplier)
                
