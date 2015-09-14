
def sayHi(engine):
	gui.ChatDialog("Hi there.").run()

def warp(engine):
	engine.effects.fader(1000, True)
	engine.warpPlayerToTile(30,30)
	engine.effects.fader(1000, False)
	
def container_search(engine):
	ts = engine.scene.actionObject
	contents = ""
	for item in ts.contents: contents += "* %s\n" % item.name
	gui.Dialog("Contents of bag:\n%s" % contents).run()
	
def loadDefaultMap(engine):
	engine.effects.fader(1000, True)
	engine.scene = engine.scene.load('../data/maps/default.map', engine)
	engine.scene.initScene()
	engine.scene.centerAt(0,0)
	engine.warpPlayerToTile(16,18)
	engine.effects.fader(1000, False)
	
def loadHutInside(engine):
	engine.effects.fader(1000, True)
	engine.scene = engine.scene.load('../data/maps/insidehut.map', engine)
	engine.scene.initScene()
	engine.scene.centerAt(0,0)
	engine.warpPlayerToTile(14,22)
	engine.effects.fader(1000, False)
	
def insideHutGiveBag1(engine): pass

def insideHutGiveBag2(engine): pass