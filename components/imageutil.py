# imageutil.py
# Slow image manipulation functions that are useful in various situations.
# by Andrew Martin (2006)
#
# TODO:
#    [x] Comment all classes
#    [x] Rename members that don't adhere to style guidelines
#    [x] Review algorithms to determine if there is a more pythonic way
#    [x] Review classes included in module for relevance to module
#

from math import ceil
import math
import pygame
import pygame.locals
import random

def createHorizontalBlendedAlphaMask(surface, start, end):
    """Takes a surface and applies an alpha mask gradient from start
    (full alpha) to end (no alpha), returns a new surface with the
    blend effect. NOTE: this is a per-pixel function, so it takes
    exponentially longer time with increasing surface dimensions.
    
    New: Stops and returns None if the original already has 
    any sort of alpha component (since this will just mess it up)
    """

    assert isinstance(start, float), "second parameter must be a float"
    assert isinstance(end, float), "third parameter must be a float"

    if start > 1.0: start = 1.0
    if end > 1.0: end = 1.0
    if start < 0.0: start = 0.0
    if end < 0.0: end = 0.0
    
    new = pygame.Surface.convert_alpha(surface)

    start_w = int(new.get_width() * start)
    end_w = int(new.get_width() * end)
    if end_w == 0: end_w = -1

    if start_w > end_w: step = -1
    else: step = 1
        
    alpha_step = 255 / abs(start_w-end_w)
    
    for h in xrange(new.get_height()):
        alpha = 255
        for w in xrange(start_w, end_w, step):            
            
            try:
                pixel = new.get_at((w,h))
                if pixel[3] < 255: return None # can't use a surface that already has alpha 
            except:
                print "Failed to retrieve pixel at (%s,%s)" % (w,h)
                return None
            
            new.set_at((w,h), (pixel[0],pixel[1],pixel[2],alpha))
            alpha -= alpha_step

    return new

def createVerticalBlendedAlphaMask(surface, start, end):
    """Takes a surface and applies an alpha mask gradient from start
    (full alpha) to end (no alpha), returns a new surface with the
    blend effect. NOTE: this is a per-pixel function, so it takes
    exponentially longer time with increasing surface dimensions.
    
    New: Stops and returns None if the original already has 
    any sort of alpha component (since this will just mess it up)
    """

    assert isinstance(start, float), "second parameter must be a float"
    assert isinstance(end, float), "third parameter must be a float"

    if start > 1.0: start = 1.0
    if end > 1.0: end = 1.0
    if start < 0.0: start = 0.0
    if end < 0.0: end = 0.0
    
    new = pygame.Surface.convert_alpha(surface)

    start_h = int(new.get_height() * start)
    end_h = int(new.get_height() * end)
    if end_h == 0: end_h = -1

    if start_h > end_h: step = -1
    else: step = 1

    alpha_step = 255 / abs(end_h - start_h)

    for w in xrange(new.get_width()):
        alpha = 255
        for h in xrange(start_h, end_h, step):
            pixel = new.get_at((w,h))
            if pixel[3] < 255: return None

            new.set_at((w,h), (pixel[0],pixel[1],pixel[2],alpha))
            alpha -= alpha_step

    return new
    
def convertToTiles(surface, width, height):
    """Takes a surface with dimensions greater than width x height
    and divides it into equal parts, each width x height in size.
    
    Returns a list of new surfaces.
    """
    
    ret = []
    
    sz = surface.get_size()
    if sz[0] == width and sz[1] == height: return [surface]
    
    xstep = int(ceil(float(sz[0]) / float(width)))
    ystep = int(ceil(float(sz[1]) / float(height)))
    
    for dy in xrange(ystep):
        for dx in xrange(xstep):
            surf = pygame.Surface((width, height)).convert_alpha()
            surf.fill((0,0,0,0))
            surf.blit(surface, (0,0), (dx*width, dy*height, width, height))
            ret.append(surf)
    
    print "Converted surface with dimensions (%d x %d) into %d tiles of dimension (%d x %d)" % \
    (surface.get_width(), surface.get_height(), len(ret), width, height)
    
    return ret
    
if __name__ == '__main__':

    # testing of functions found within this file:

    pygame.display.init()
    scr = pygame.display.set_mode((800,600))

    img = pygame.image.load('../data/tilesets/base/grass1.png')
    himg = createHorizontalBlendedAlphaMask(img, 0.2, 1.0)
    himg2 = createHorizontalBlendedAlphaMask(img, 0.8, 0.0)
    vimg = createVerticalBlendedAlphaMask(img, 0.2, 1.0)
    vimg2 = createVerticalBlendedAlphaMask(img, 0.8, 0.0)    

    done = False

    scr.fill((255,255,255))

    scr.blit(img, (0,0))
    scr.blit(himg, (0,50))
    scr.blit(himg2, (0,100))
    scr.blit(vimg, (50,50))
    scr.blit(vimg2, (50,100))

    pygame.display.update()

    while not done:
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.locals.KEYDOWN:
                if e.key == pygame.locals.K_ESCAPE:
                    done = True
                    
        pygame.time.wait(60)

