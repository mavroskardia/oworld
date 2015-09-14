import sys
from engine import Engine

def PassesRequirements():
    try:
        import pygame
    except: 
        return False
    
    return True

def PrintRequirements():
    overworldRequirements = """
Overworld Requirements:

    Pygame (http://www.pygame.org)
    """
    
    sys.__stderr__.write(overworldRequirements)  

if __name__ == '__main__': 
    if (PassesRequirements()):
        Engine().run()
    else:
        PrintRequirements()
        
