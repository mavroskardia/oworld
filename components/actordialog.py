from zipfile import ZipFile
import configuration
import gui
import os
import types

class ActorDialog(gui.ChatDialog):
    
    def __init__(self, character, text, **kwargs):
        gui.ChatDialog.__init__(self, text, **kwargs)
        
        self.characterPortrait = gui.Image(parent=self, surface=character._spriteset[2][0], pos=(5,5))
        self.add(self.characterPortrait)
        
        self.characterName = gui.Label(parent=self, text=character.name)
        self.characterName.x = self.characterPortrait.right + 5
        self.characterName.y = self.characterPortrait.y + self.characterPortrait.height/2 - self.characterName.height/2
        self.add(self.characterName)
        
        self.textLabel.x = 5
        self.textLabel.y = self.characterPortrait.bottom + 10
        
        self.height = 30 + self.characterPortrait.height + self.textLabel.height
        
class ActorDialogWithYesNo(ActorDialog):
    
    def clickYes(self, event, button):
        self.result = True
        self.exit()
        
    def clickNo(self, event, button):
        self.result = False
        self.exit()
    
    def keypress(self, event):
        if event.key == K_RETURN:
            if not self.textLabel.chatting:
                self.result = True
                self.exit()
    
    def __init__(self, character, text, **kwargs):
        ActorDialog.__init__(self, character, text, **kwargs)
        if self.width < 210: self.width = 210
        self.result = False
        bc = (self.backgroundColor[0], self.backgroundColor[1], self.backgroundColor[2], 255)        
        self.yesButton = gui.Button(text="Yes", callback=self.clickYes, parent=self, backgroundColor=bc)
        self.height += self.yesButton.height + 10
        self.yesButton.width = 100
        self.yesButton.x = self.width / 2 - self.yesButton.width / 2 - 90
        self.yesButton.y = self.height - self.yesButton.height - 10
        self.noButton = gui.Button(text="No", callback=self.clickNo, parent=self, backgroundColor=bc)
        self.noButton.width = 100
        self.noButton.x = self.width / 2 + self.noButton.width / 2 - 10
        self.noButton.y = self.height - self.noButton.height - 10
        self.yesButton.show = False
        self.noButton.show = False
        self.add(self.yesButton)
        self.add(self.noButton)
        
    def render(self, surface):
        ActorDialog.render(self, surface)
        if not self.textLabel.chatting:
            self.yesButton.show = True
            self.noButton.show = True    
