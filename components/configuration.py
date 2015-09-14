# 
# All general Overworld configuration should go in this file.
#

import os

screen_resolution = (1024, 768)

datadir = os.path.join('..', 'data')
mapdir = os.path.join(datadir, 'maps')
spritesetdir = os.path.join(datadir, 'spritesets')
tilesetdir = os.path.join(datadir, 'tilesets')
scriptdir = os.path.join(datadir, 'scripts')
dialogdir = os.path.join(datadir, 'dialogs')
itemdir = os.path.join(datadir, 'items')
fontdir = os.path.join(datadir, 'fonts')
regfont = os.path.join(fontdir, 'Vera.ttf')
monofont = os.path.join(fontdir, 'VeraMono.ttf')

spritesets = os.path.join(datadir, 'spritesets.zip')
tilesets = os.path.join(datadir, 'tilesets.zip')
scripts = os.path.join(datadir, 'scripts.zip')
dialogs = os.path.join(datadir, 'dialogs.zip')
items = os.path.join(datadir, 'items.zip')

default_grid_width = 32
default_grid_height = 32
default_width_in_tiles = 100
default_height_in_tiles = 100
default_tile_width = 32
default_tile_height = 32

default_tileset = "default"
default_actor_spriteset = "chryso"
default_itemset = "default"
default_scriptset = "default"
default_dialogset = "default"

    
