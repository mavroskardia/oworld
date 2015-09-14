#
# Scene
#
# Goal: Object that controls all world data for a particular "scene".
#		This includes handling all visual and logic elements.
#		Sub-objects included: Tilestacks, Actors, Triggers, and a Viewport
# by Andrew Martin (2006)
#
# TODO:
#	[] Comment all classes
#	[] Rename members that don't adhere to style guidelines
#	[] Review algorithms to determine if there is a more pythonic way
#	[] Review classes included in module for relevance to module
#

from actordialog import ActorDialog
from characters import Actor, Spriteset
from math import ceil, floor
from pygame.locals import *
from subscreens import CharacterScreen
from tiles import TileFactory, Tile, Tilestack
from zipfile import ZipFile, ZIP_DEFLATED
import configuration
import dataset
import collectors
import gui
import os
import pygame
import stat
import types
import xml.dom.minidom

class ScriptRunner(object):
	"Houses all OverWorld scripts for execution at a moment's notice!"
	
	def __init__(self, scene):
		self.engine = scene.engine
		self.scene = scene
		self._scripts = {}		

	def addScripts(self, script):
		if not isinstance(script, str) or script == None or script == "":
			return
		
		# clean up the script 
		script = script.replace('\r', '') 
		if not script.endswith('\n'): script = script+"\n"
		
		l = {'engine':self.engine, 'scene':self.scene, 'gui':gui}
		g = {}		
		try: exec(script,l,g)
		except SyntaxError, e:
			print "Failed to add script: %s" % e
			return
		
		for i in g:
			if type(g[i]) == types.FunctionType:
				print "Found function \"%s\", adding to scripts" % i
				self._scripts[i]=g[i]				
			else:
				print "Skipping %s: %s" % (type(g[i]), i)

	def addDefaultScripts(self):
		zf = ZipFile(configuration.scripts)
		scripts = dataset.splitSets(zf.namelist())
		
		for script in scripts[configuration.default_scriptset]:
			self.addScripts(zf.read(script))

	def addScriptsByFile(self, fn):
		f = open(fn)
		r = f.read()
		f.close()
		self.addScripts(r)
		
	def addScriptsByDir(self, d):
		files = []
		for root, dirs, files in os.walk(d):
			for fs in files:
				files.append(os.path.join(w[0], fs))

		for f in files:
			if f.endswith('.ows'): self.addScriptsByFile(f)

	def execute(self, script_id):
		try: self._scripts[script_id](self.engine)
		except KeyError: print "Failed to execute non-existent script \"%s\"" % script_id

class Viewport(object):
	"""The viewport acts as the "camera" for the scene. It keeps track
	of the current "virtual" pixel and translates that into absolute
	pixels for render time.
	"""
	
	DefaultWidth = 800
	DefaultHeight = 600
	
	def __init__(self, scene):
		self.scene = scene
		self.widthInPixels, self.heightInPixels = 0, 0
		self.x, self.y = 0, 0
		if not pygame.display.get_surface():
			self.widthInPixels = Viewport.DefaultWidth
			self.heightInPixels = Viewport.DefaultHeight
		else:
			self.widthInPixels, self.heightInPixels = pygame.display.get_surface().get_size()
		
	def __get_x(self): return self.__x
	def __set_x(self, val):
		self.__x = val
		if self.__x < 0: self.__x = 0
		if self.__x > self.scene.widthInPixels - self.widthInPixels:
			self.__x = self.scene.widthInPixels - self.widthInPixels
	x = property(__get_x, __set_x, None, "X coordinate of topleft")
	
	def __get_y(self):
		return self.__y
	def __set_y(self, val):
		self.__y = val
		if self.__y < 0: self.__y = 0
		if self.__y > self.scene.heightInPixels - self.heightInPixels:
			self.__y = self.scene.heightInPixels - self.heightInPixels
	y = property(__get_y, __set_y, None, "Y coordinate of topleft")
	
	def __repr__(self):
		return "(%d, %d)" % (self.x, self.y)
	
	def center(self, x, y):
		self.x = x - (self.widthInPixels/2)
		self.y = y - (self.heightInPixels/2)
		
	def isOnEdge(self):
		return self.x == 0 or self.y == 0
	
class Scene(object):
	"""Represents all visual and logic elements for an individual map
	and its workings (e.g. actors, tilestacks, etc)
	"""
	
	### Private Methods ###
	
	def __init__(self, engine, **keywords):
		"Construct a Scene object"
		self.engine = engine
		
		self.widthInTiles = keywords['widthInTiles'] if 'widthInTiles' in keywords else configuration.default_width_in_tiles
		self.heightInTiles = keywords['heightInTiles'] if 'heightInTiles' in keywords else configuration.default_height_in_tiles
		self.tileWidth = keywords['tileWidth'] if 'tileWidth' in keywords else configuration.default_tile_width
		self.tileHeight = keywords['tileHeight'] if 'tileHeight' in keywords else configuration.default_tile_height
		self.tileFactory = keywords['tileFactory'] if 'tileFactory' in keywords else TileFactory(configuration.default_tileset, self.tileWidth, self.tileHeight)
		self.borderUnwalkable = keywords['borderUnwalkable'] if 'borderUnwalkable' in keywords else False
		self.borderTrigger = keywords['borderTrigger'] if 'borderTrigger' in keywords else False
		self.itemset = keywords['itemset'] if 'itemset' in keywords else configuration.default_itemset
		self.partySpacing = keywords['partySpacing'] if 'partySpacing' in keywords else 40
		self.partySpeed = keywords['partySpeed'] if 'partySpeed' in keywords else 2
		self.baseTile = keywords['baseTile'] if 'baseTile' in keywords else self.tileFactory.specialTiles['base']
		self.properties = keywords
		self.widthInPixels = self.widthInTiles * self.tileFactory.tileWidth
		self.heightInPixels = self.heightInTiles * self.tileFactory.tileHeight
		self.actors = []
		self.players = []
		self.triggers = []
		self.scripts = []
		
		self.triggerTile = None
		self.actionObject = None

		self.viewport = Viewport(self)
		self.scriptRunner = ScriptRunner(self)
		
	def initScene(self):
		"Auxiliary init method for portions of init that vary after standard init"
		if not hasattr(self, 'tilestacks') or not self.tilestacks: self.tilestacks = self._loadTilestacks()

		self.players = self.properties['players'] if 'players' in self.properties else [Actor(self, configuration.default_actor_spriteset)]
		
		if self.player.px == 0: self.player.px = self.player.width
		if self.player.py == 0: self.player.py = self.player.height

		self.scriptRunner.addDefaultScripts()
		self.itemCollector = collectors.ItemCollector(self, self.itemset)
		self.dialogCollector = collectors.DialogCollector(self, configuration.default_dialogset)
		
	def __get_player(self):
		if len(self.players) > 0:
			return self.players[0]
		else:
			raise Exception, "Scene has no players"
	def __set_player(self, player): 
		if len(self.players) > 0: self.players[0] = player
		else: self.players.insert(0, player)
	player = property(__get_player, __set_player, None, "Gets/Sets the controlling player")
		
	def _loadTilestacks(self):
		ret = []
		for y in xrange(self.heightInTiles):
			for x in xrange(self.widthInTiles):
				ts = Tilestack()
				ts.addBaseTile(Tile(self.tileFactory, self.baseTile))
				ret.append(ts)
				
		return ret
		
	def _drawGrid(self, surface):
		"""Draws a grid overlaying the viewport, used internally by the render
		method.
		"""
		
		if "drawGrid" not in self.properties or not self.properties["drawGrid"]: return
		
		gridWidth = self.properties["gridWidth"] if "gridWidth" in self.properties else Scene.DefaultGridWidth
		gridHeight = self.properties["gridHeight"] if "gridHeight" in self.properties else Scene.DefaultGridHeight			
			
		# vertical lines first:
		xpos = -(self.viewport.x % gridWidth)
		while xpos < surface.get_width():
			xpos += gridWidth
			pygame.draw.line(surface, (200,200,200,150), (xpos,0), (xpos, surface.get_height()))
			
		# horizontal lines:
		ypos = -(self.viewport.y % gridHeight)
		while ypos < surface.get_height():
			ypos += gridHeight
			pygame.draw.line(surface, (200,200,200,150), (0,ypos), (surface.get_width(), ypos))

	def _drawTiles(self, surface, drawBaseTiles=True):
		"""Internal method used by the external method render. 
		NOTE: this method is called EVERY render cycle, and therefore needs to be as 
		optimized as possible.
		"""
		tw = self.tileFactory.tileWidth
		th = self.tileFactory.tileHeight
		txstart = int(ceil(self.viewport.x / tw))
		tystart = int(ceil(self.viewport.y / th))
		txend = int(ceil(self.viewport.widthInPixels / tw)) + txstart + 1
		tyend = int(ceil(self.viewport.heightInPixels / th))+ tystart + 2
		if txend >= self.widthInTiles: txend = self.widthInTiles
		if tyend >= self.heightInTiles: tyend = self.heightInTiles
		ox = -(self.viewport.x % self.tileFactory.tileWidth)
		oy = -(self.viewport.y % self.tileFactory.tileHeight)
		px, py = ox, oy
		
		if drawBaseTiles:
			for y in xrange(tystart, tyend):
				for x in xrange(txstart, txend):
					try:
						ts = self.tilestacks[y*self.widthInTiles + x]
						ts.renderBase(surface, px, py)
						if not ts.isWalkable and self.borderUnwalkable:						
							pygame.draw.rect(surface, (0,100,0,50), (px,py,tw,th), 1)
						if ts.triggerId and self.borderTrigger:
							pygame.draw.rect(surface, (0,0,100,50), (px+1,py+1,tw-2,th-2), 1)
						px += tw
					except: surface.fill((0,0,0), (px, py, tw, th))
				py += th
				px = ox
		else:
			for y in xrange(tystart, tyend):
				for x in xrange(txstart, txend):
					try:
						ts = self.tilestacks[y*self.widthInTiles + x]
						ts.renderRoof(surface, px, py)
						if not ts.isWalkable and self.borderUnwalkable:
							pygame.draw.rect(surface, (0,100,0,50), (px,py,tw,th), 1)
						if ts.triggerId and self.borderTrigger:
							pygame.draw.rect(surface, (0,0,100,50), (px+1,py+1,tw-2,th-2), 1)
						px += tw
					except: pass
				py += th
				px = ox

	def _drawActors(self, surface):
		"""Draws all actors in their z-order based upon y position.
		Note: this method is called every cycle so needs to be optimized.
		"""
		
		# sort all actors in increasing y order
		drawList = self.actors + self.players
		drawList.sort(lambda x,y: x.py-y.py)	# this is why i love python		
		for actor in drawList: actor.render(surface, -self.viewport.x, -self.viewport.y)
		
	### Public Methods ###
	
	def changeSize(self, width, height):
		"Changes the map size. Width and height parameters are in tiles."
		
		self.properties["tile_width"] = width
		self.properties["tile_height"] = height
		self.widthInTiles = width
		self.widthInPixels = width * self.tileFactory.tileWidth
		self.heightInTiles = height
		self.heightInPixels = height * self.tileFactory.tileHeight
		
	def render(self, surface):
		"Renders the scene through the viewport onto the specified surface."

		self._drawTiles(surface, True)
		self._drawGrid(surface)		
		self._drawActors(surface)
		self._drawTiles(surface, False)
		
	def update(self, tick):
		"Updates the scene logic on a clock-based interval"
		
		prx, pry = self.player.px, self.player.py
		self.player.px -= self.viewport.x
		self.player.py -= self.viewport.y
		self.player.update(tick)
		self.player.px, self.player.py = prx, pry
		
		for i in xrange(1,len(self.players)): self.players[i].update(tick)
						
		for sscript in self.scripts:
			sscript.update(tick)
		for npc in self.actors:
			npc.update(tick)
	
	def centerAt(self, x, y):
		"Centers the viewport at the x,y coordinate specified."
		self.viewport.center(x, y)
	
	def moveViewport(self, dx, dy):
		"Moves the viewport in the direction(s) specified by dx and dy"
		self.viewport.x += dx
		self.viewport.y += dy
		
	def setPartySpeed(self, speed):
		self.partySpeed = speed
		
	def moveParty(self, dx, dy):
		dx *= self.partySpeed
		dy *= self.partySpeed
		stepx = abs(dx)
		stepy = abs(dy)
		if stepx == 0: stepx = self.player._stepx
		if stepy == 0: stepy = self.player._stepy
		
		self.movePlayer(self.player, dx, dy)
		
		for i in xrange(1, len(self.players)):
			o,p = self.players[i-1], self.players[i]

			ps = self.partySpacing
			
			if o.direction == Spriteset.EAST: # going right
				if p.width > ps: ps = p.width
				# should the successor move east as well?
				if p.px < o.px-ps: self.movePlayer(p, stepx, 0)
				# should the successor move up/down to match predecessor?
				if p.py > o.py+stepy: self.movePlayer(p, 0, -stepy)
				elif p.py < o.py-stepy: self.movePlayer(p, 0, stepy)
			elif o.direction == Spriteset.WEST: # going left
				# move west as well?
				if p.px > o.px+ps: self.movePlayer(p, -stepx, 0)
				# move up/down?
				if p.py > o.py+stepy: self.movePlayer(p, 0, -stepy)
				elif p.py < o.py-stepy: self.movePlayer(p, 0, stepy)
			elif o.direction == Spriteset.NORTH:
				# move east/west?
				if p.px > o.px+stepx: self.movePlayer(p, -stepx, 0)
				elif p.px < o.px-stepx: self.movePlayer(p, stepx, 0)
				# move up as well?
				if p.py > o.py+ps: self.movePlayer(p, 0, -stepy)
			elif o.direction == Spriteset.SOUTH:				
				# move east/west?
				if p.px > o.px+stepx: self.movePlayer(p, -stepx, 0)
				elif p.px < o.px-stepx: self.movePlayer(p, stepx, 0)
				# move down as well?
				if p.py < o.py-ps: self.movePlayer(p, 0, stepy)
			else:
				raise Exception, "Impossible sprite direction: %s" % o.direction   
		
	def movePlayer(self, player, dx, dy):
		"Moves the player in the direction(s) specified by dx and dy"
		
		player.move((dx, dy))
		
		tx = player.px / self.tileFactory.tileWidth
		ty = player.py / self.tileFactory.tileHeight
		
		try:
			
			ts1 = self.tilestacks[ty*self.widthInTiles+tx]
			triggerTile = ts1			
			
			if dx > 0: # right
				ts2 = self.tilestacks[ty*self.widthInTiles+tx+1]
				ts3 = self.tilestacks[(ty-1)*self.widthInTiles+tx+1]
				triggerTile = ts2
			elif dx < 0: # left
				ts2 = self.tilestacks[(ty-1)*self.widthInTiles+tx]
				ts3 = ts2
			elif dy < 0: # up
				ts1 = self.tilestacks[(ty-1)*self.widthInTiles+tx]
				ts2 = self.tilestacks[(ty-1)*self.widthInTiles+tx+1]
				ts3 = ts2
				triggerTile = ts2
			elif dy > 0: # down
				#ts1 = self.tilestacks[ty*self.widthInTiles+tx]
				ts2 = self.tilestacks[ty*self.widthInTiles+tx+1]
				ts3 = ts2
			else:
				ts2 = ts1
				ts3 = ts2
				
			if triggerTile != self.triggerTile: self.triggerTile = None
				
			if False in (ts1.isWalkable, ts2.isWalkable, ts3.isWalkable):
				d = player.direction
				player.move((-dx,-dy))
				player.direction = d
				
			npc = self.npcAt((player.px+(player.width>>1), player.py+(player.height>>1)))
			if npc:
				#npc.move(dx,dy) -- uncomment this to enable npc "pushing"
				d = player.direction
				player.move((-dx,-dy))
				player.direction = d
				
			if not self.triggerTile and triggerTile.triggerId:
				ts1.performAction(self)
				#self.scriptRunner.execute(ts1.triggerId)
				self.triggerTile = ts1
				
		except IndexError:				
			d = player.direction
			player.move((-dx,-dy))
			player.direction = d
						
	def npcAt(self, collisionPoint):
		"Returns true if there is an npc sprite standing in the range of collisionPoint +/- tolerance"
		ret = None
		cx = collisionPoint[0]
		cy = collisionPoint[1]
		for npc in self.actors:
			r = npc.getRect()
			if r[0] <= cx and r[0]+r[2] >= cx:
				if r[1] <= cy and r[1]+r[3] >= cy:
					ret = npc
					break
			elif r[0] >= cx and r[0]+r[2] <= cx:
				if [r1] >= cy and r[1]+r[3] <= cy:
					ret = npc
					break

		return ret
		
	def addBaseTile(self, tileIndex, x, y):		
		ts = self.tilestacks[y*self.widthInTiles+x]
		ts.addBaseTile(Tile(self.tileFactory, tileIndex))
		ts.isWalkable = False
		
	def addRoofTile(self, tileIndex, x, y):
		self.tilestacks[y*self.widthInTiles+x].addRoofTile(Tile(self.tileFactory, tileIndex))
		
	def getTilestackAt(self, x, y):
		tx = x / self.tileFactory.tileWidth
		ty = y / self.tileFactory.tileHeight
		try: return self.tilestacks[ty*self.widthInTiles+tx]
		except Exception, e:
			raise Exception, "Could not retrieve tilestack at (%d,%d): %s" % (tx,ty,e)
		
	def addScript(self, scriptId, timeout=1000):
		"Runs the specified scriptId (through the ScriptRunner) every /timeout/ seconds."
		self.scripts.append(SceneScript(self, scriptId, timeout))
		
	def removeScript(self, scriptId):
		for script in self.scripts:
			if script.scriptId == scriptId: 
				self.scripts.remove(script)
				break			
		
	def performPlayerAction(self):
		"""Figure out if there is any actionable object in front of the player, then do 
		the appropriate action to that object.		
		"""
		
		if self.player.direction == Spriteset.EAST: # right, good
			obj = self.getObjectAt((self.player.px+self.player.width, self.player.py+self.player.height/2))
		elif self.player.direction == Spriteset.NORTH: # up, good
			obj = self.getObjectAt((self.player.px+self.player.width/2, self.player.py))			
		elif self.player.direction == Spriteset.SOUTH: # down, acceptable (a little too much space)
			obj = self.getObjectAt((self.player.px+self.player.width/2, self.player.py+(2*self.player.height/3)))
		elif self.player.direction == Spriteset.WEST: # left, good
			obj = self.getObjectAt((self.player.px, self.player.py+self.player.height/2))

		if not obj: return
		else:			
			if isinstance(obj, Actor): obj.performDialog()
			elif isinstance(obj, Tilestack): obj.performAction(self)
						
	def getObjectAt(self, point):
		"Determine if there is an npc or a unwalkable tile with a trigger at the point specified"

		npc = self.npcAt(point)
		if npc: return npc
				
		ts = self.getTilestackAt(point[0], point[1])
		if not ts.isWalkable and ts.triggerId != None and ts.triggerId != "": return ts
		
		return None
			
	def createCharacter(self):
		"Show the character editor with default values, return the character edited."
		ce = CharacterScreen(Actor(self, configuration.default_actor_spriteset), editable=True)
		ce.run()
		return ce.character
	
	def playDialog(self, character, txt, **kwargs):
		ActorDialog(character, txt, **kwargs).run()
		
	def playDialogWithYesNo(self, character, txt, **kwargs):
		cd = ActorDialogWithYesNo(character, txt, **kwargs)
		cd.run()
		return cd.result
	
	def displayShopInterface(self, buyer, seller):
		"""Builds the store interface using the specified actor's inventory. Although it isn't terribly
		realistic, all shopkeepers have the same prices for items"""
		ShopInterface(self, buyer, seller).run()
	
	def addPlayerToParty(self, player):
		player.px = self.players[-1].px - self.partySpacing
		player.py = self.players[-1].py - self.partySpacing
		self.players.append(player)
		
	def addActorToScene(self, actor):
		self.actors.append(actor)
		
	def createMapContainer(self, contents, x=-1, y=-1):
		"""Creates a container object at the specified pixel coordinates that can 
		then be interacted with by the player.
		"""
		if x == -1: x = self.player.px+self.player.width
		if y == -1: y = self.player.py
		print "adding %s to tile at (%s,%s)" % (contents, x, y)
		if not isinstance(contents, list): contents = [contents]
		
		ts = self.getTilestackAt(x,y)		
		if ts.triggerId:
			if ts.triggerId != "container_search": raise Exception, "Cannot create container on tile containing existing trigger (%d,%d)" % (x,y)
			else: ts.contents += contents				
		else:
			ts.addBaseTile(Tile(self.tileFactory, self.tileFactory.specialTiles['generic_container']))
			ts.triggerId = "container_search"
			if not ts.contents: ts.contents = contents
			else: 
				for item in contents:
					if item not in ts.contents: ts.contents += [item]
		
	def save(self, filename):
		"""Saves the scene to the specified filename."""
		# What all needs to be saved for a scene?:
		#	map info (tileset, tile index, trigger, etc)
		#	actor info (player and npcs)
		#	script info
		#	anything else?
		
		if os.path.exists(filename):
			ynd = gui.Dialog.createYesNoDialog('Overwrite existing "%s"?' % filename)
			ynd.run()
			if not ynd.result: return
		
#		self.widthInPixels = self.widthInTiles * self.tileFactory.tileWidth
#		self.heightInPixels = self.heightInTiles * self.tileFactory.tileHeight
#		self.actors = []
#		self.tilestacks = self._loadTilestacks()
#		self.triggers = []
#		self.viewport = Viewport(self)
#
#		if "actor_spriteset" in self.properties:
#			self.player = Actor(self.properties["actor_spriteset"])
#		else:
#			self.player = Actor(self, Scene.DefaultActorSpriteset)
#
#		self.tileSelector = TileSelector(self)		
#		
#		self.scriptRunner = ScriptRunner(self)
#		self.scriptRunner.addScriptsByDir("../data/scripts")
#		self.scripts = []
#		self.triggerTile = None		
#		
#		self.itemCollector = ItemCollector(self, self.itemset)
#			
#		self.characterEditor = CharacterEditor()

		print "Creating scene xml..."

		scene_xml = xml.dom.minidom.Document()
		
		sceneXml = xml.dom.minidom.Element("scene")		
		
		# tile factory
		scene_tf_xml = xml.dom.minidom.Element("tilefactory")
		scene_tf_xml.attributes["tileset"] = self.tileFactory.tileset
		scene_tf_xml.attributes["tilewidth"] = "%s" % self.tileFactory.tileWidth
		scene_tf_xml.attributes["tileheight"] = "%s" % self.tileFactory.tileHeight
		sceneXml.appendChild(scene_tf_xml)
		
		# itemset
		scene_is_xml = xml.dom.minidom.Element("itemset")
		scene_is_xml.attributes["itemset"] = self.itemset
		
		# actors
		scene_actors_xml = xml.dom.minidom.Element("actors")
		
		# player party
		scene_pp_xml = xml.dom.minidom.Element("playerparty")
		
		# map tilestacks
		scene_tile_xml = xml.dom.minidom.Element("tilestacks")
		scene_tile_xml.attributes["width"] = "%s" % self.widthInTiles
		scene_tile_xml.attributes["height"] = "%s" % self.heightInTiles
		
		for t in self.tilestacks: scene_tile_xml.appendChild(t.toXml())
		
		sceneXml.appendChild(scene_tile_xml)
		
		scene_xml.appendChild(sceneXml)
		
		sceneStr = scene_xml.toxml()
		
		print "Finished creating scene xml"
		
		print "Compressing and writing scene xml..."
		f = ZipFile(filename, 'w', ZIP_DEFLATED)		
		f.writestr("scene.xml", sceneStr)
		f.close()
		print "Wrote scene to file %s in %d bytes" % (filename, os.stat(filename)[stat.ST_SIZE])
		
	@staticmethod
	def load(filename, engine, progressDialog=None):
		"""Loads a new scene object."""
		
		if not os.path.exists(filename):
			gui.ErrorDialog("No file by the name \"%s\" found." % filename).run()
			return
		
		print 'Loading scene from "%s"...' % filename
		
		f = ZipFile(filename)
		try: sceneXmlStr = f.read("scene.xml")
		except Exception, e: 
			gui.ErrorDialog("Could not read scene.xml file, aborting load (%s)" % e).run()
			f.close()
			return
		
		f.close()
		
		if progressDialog: progressDialog.updateProgress(10)
				
		print "Parsing scene xml..."
		sceneXml = xml.dom.minidom.parseString(sceneXmlStr)
		print "Finished parsing scene xml"

		if progressDialog: progressDialog.updateProgress(10)
		
		# tile factory
		scene_tf_xml = sceneXml.getElementsByTagName("tilefactory")[0]
		tw = int(scene_tf_xml.attributes["tilewidth"].value)
		th = int(scene_tf_xml.attributes["tileheight"].value)
		print 'TileFactory standard tilesize: %dx%d' % (tw, th)
		tf = TileFactory(scene_tf_xml.attributes["tileset"].value, tw, th)

		if progressDialog: progressDialog.updateProgress(10)
		
		# tilestacks
		scene_tile_xml = sceneXml.getElementsByTagName("tilestacks")[0]
		tilestacks = []
		# tilestacks attributes
		widthInTiles = int(scene_tile_xml.attributes['width'].value)
		heightInTiles = int(scene_tile_xml.attributes['height'].value)
		print "Scene tile width/height: %d x %d" % (widthInTiles, heightInTiles)
		print "Removing non-element child nodes..."
		tilestacksXml = [i for i in scene_tile_xml.childNodes if i.nodeType == xml.dom.minidom.Node.ELEMENT_NODE]
		print "Done removing non-element child nodes"
		
		if progressDialog: progressDialog.updateProgress(10)
		
		totalTilestacks = len(tilestacksXml)
		print "Total tilestacks to parse: %d" % totalTilestacks
		
		print "Parsing tilestacks..."
		# tilestacks children
		count = 0
		for txml in tilestacksXml: 
			tilestacks.append(Tilestack.fromXml(txml, tf))
			count += 1
			if progressDialog and count > totalTilestacks/30: 
				progressDialog.updateProgress(1)
				count = 0
		print "Finished parsing tilestacks (parsed %s tilestacks)" % len(tilestacks)
		
		ret = Scene(engine, tileFactory=tf, widthInTiles=widthInTiles, heightInTiles=heightInTiles)
		ret.tilestacks = tilestacks
		if progressDialog: progressDialog.updateProgress(10)

		ret.initScene()
		if progressDialog: progressDialog.updateProgress(10)

		
		# TEMPORARY
		ret.player = Actor(ret, configuration.default_actor_spriteset)
		ret.scriptRunner.addDefaultScripts()
		ret.itemCollector = ItemCollector(ret, ret.itemset)
		
		print 'Finished loading scene'

		if progressDialog: progressDialog.updateProgress(10)

		return ret
		
class SceneScript(object):
	"Container for the scripts that run throughout the scene. This manages the timeouts, etc"
	
	def __init__(self, scene, scriptId, timeout=0):
		self.scene = scene
		self.scriptId = scriptId
		self.timeout = timeout
		self.runOnce = self.timeout == 0
		self.dt = 0
		
	def update(self, ticks):
		self.dt += ticks		
		if self.dt > self.timeout:
			self.scene.scriptRunner.execute(self.scriptId)
			if self.runOnce: self.scene.scripts.remove(self)
			else: self.dt = 0
