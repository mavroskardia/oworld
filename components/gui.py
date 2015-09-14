# gui.py
# Subscreen GUI Code
# by Andrew Martin (2006-2007)
#
# TODO:
#	[] Comment all classes
#	[] Rename members that don't adhere to style guidelines
#	[] Review algorithms to determine if there is a more pythonic way
#	[] Review classes included in module for relevance to module
#

from math import pi, floor
from pygame.locals import *
import pygame
import sys
import threading

DefaultControlBackground = (0x88, 0x88, 0x88)
DefaultControlBackground2 = (0xaa, 0xaa, 0xaa)
DefaultControlBackground3 = (0x88, 0x88, 0x88)
DefaultControlBorderColor = (0,0,0,255)
DefaultControlBorderWidth = 1
DefaultControlHighlight = (187,221,255,255)
DefaultApplicationIdleTime = 50
DefaultFontColor = (255,255,255,255)

class GuiException(Exception): pass

class Control(object):
	
	def __init__(self, **kwargs):
		
		self.children = []
		self.show = True
		self.parent = kwargs['parent'] if 'parent' in kwargs else None		
		self.x, self.y = kwargs['pos'] if 'pos' in kwargs else (0,0)
		self.xOffset, self.yOffset = 0, 0
		self.width = kwargs['width'] if 'width' in kwargs else 0
		self.height = kwargs['height'] if 'height' in kwargs else 0
		self.curWidth, self.curHeight = 0, 0
		self.mouseOverControls = []
		self.mouseDownControls = []
		self.onTop = False
		self.animateInit = kwargs['animateInit'] if 'animateInit' in kwargs else lambda x: ()
		self.animateFunc = kwargs['animateFunc'] if 'animateFunc' in kwargs else lambda x,y: ()
		self.animateInited = False
		self.enabled = True
	
	def __repr__(self): return "Abstract Control"
	
	def __get_abs_x(self): 
		compx = self.x + self.xOffset
		p = self.parent
		while True:
			if p:
				compx += p.x + p.xOffset
				p = p.parent
			else: break
		return compx
	absx = property(__get_abs_x)
		
	def __get_abs_y(self): 
		compy = self.y + self.yOffset
		p = self.parent
		while True:
			if p:
				compy += p.y + p.yOffset
				p = p.parent
			else: break
		return compy
	absy = property(__get_abs_y)
	
	def __get_rot(self): return self.__render_on_top
	def __set_rot(self, rot):
		for c in self.children: c.renderOnTop = rot
		self.__render_on_top = rot
	def __del_rot(self): del self.__render_on_top
	renderOnTop = property(__get_rot, __set_rot, __del_rot, "Render above all other controls")

	def __get_show(self): return self.__show
	def __set_show(self, show): 
		for c in self.children: c.show = show
		self.__show = show
	def __del_show(self): del self.__show
	show = property(__get_show, __set_show, __del_show, "Show this control during rendering and events")
	
	def __getanc(self):
		p = self.parent
		while True:
			if p and p.parent: p = p.parent
			else: break
		return p
	ancestor = property(__getanc, None, None, "Return the ancestor of this control")
		
	def __get_right(self): return self.x + self.width
	def __set_right(self, rx):
		if rx >= self.x: self.width = rx - self.x			
	right = property(__get_right, __set_right, None, "Gets/Sets the rightmost x coordinate of the control")
	
	def __get_bottom(self): return self.y + self.height
	def __set_bottom(self, ry): 
		if ry >= self.y: self.height = ry - self.y
	bottom = property(__get_bottom, __set_bottom, None, "Gets/Sets the bottommost y coordinate of the control")
	
	def __get_show(self): return self.__show
	def __set_show(self, show):
		for c in self.children: c.show = show
		self.__show = show
	def __del_show(self): del self.__show
	show = property(__get_show, __set_show, __del_show, "Should or should not show this control and its children")
	
	def preRender(self, surface): pass
	def postRender(self, surface): pass
				
	def render(self, surface):
		self.update(self)

		tmpSurface = pygame.Surface((self.width, self.height)).convert_alpha()
		
		if not self.animateInited: 
			self.animateInit(self)
			self.animateInited = True

		self.animateFunc(self, tmpSurface)
		
		self.preRender(tmpSurface)
		
		self.children.sort(lambda x,y: 1 if x.onTop and not y.onTop else -1 if y.onTop and not x.onTop else 0)	# this is why i love python

		for c in self.children:
			if c.show: c.render(tmpSurface)
			
		self.postRender(tmpSurface)

		if not self.enabled: tmpSurface.fill((0,0,0,50))

		surface.blit(tmpSurface, (self.x+self.xOffset, self.y+self.yOffset))
					
	def handleEvents(self, events=None):
		if events is None: events = pygame.event.get()
		
		for e in events:
			if e.type == pygame.MOUSEMOTION: self.mouseMotion(e)						
			elif e.type == pygame.MOUSEBUTTONDOWN: self.mouseDown(e)
			elif e.type == pygame.MOUSEBUTTONUP: self.mouseUp(e)
			elif e.type == pygame.QUIT: self.done = True						
			elif e.type == pygame.KEYDOWN: self.keypress(e)
		
	def mouseMotion(self, event):
		for c in self.controlsAt(event): c.mouseMotion(event)
		newMouseOvers = self.controlsAt(event)
		for c in newMouseOvers:
			if c not in self.mouseOverControls:
				self.mouseOverControls.append(c)
				c.mouseEnter(event)
			c.mouseMotion(event)
			
		for c in self.mouseOverControls:
			if c not in newMouseOvers: c.mouseLeave(event)
				
		self.mouseOverControls = newMouseOvers
		
	def mouseUp(self, event):
		for c in self.mouseDownControls: c.mouseUp(event)
		for c in set(self.controlsAt(event)):
			if c in self.mouseDownControls: c.clicked(event, c)
			else: c.mouseUp(event)
			
	def mouseDown(self, event):
		self.mouseDownControls = []
		for c in set(self.controlsAt(event)):
			self.mouseDownControls.append(c)
			c.mouseDown(event)
			
	def clicked(self, event, control): pass
	def mouseEnter(self, event): pass
	def mouseLeave(self, event): pass
	def update(self, control): pass
	def keypress(self, event):
		for c in self.children: c.keypress(event)
		
	def add(self, control):
		assert isinstance(control, Control)
		control.parent = self
		self.children.append(control)
		control.added(self)
		
	def added(self, parent): pass
		
	def remove(self, control):
		if control in self.children: self.children.remove(control)
	
	@staticmethod	
	def highlightColor(color, colorDx=30):
		newc = []
		for c in color:
			nc = c+colorDx
			if nc > 255: nc = 255
			if nc < 0: nc = 0
			newc.append(nc)
			
		return tuple(newc)
	
	def isMouseOver(self, event, control):
		x,y = event.pos		
		absx, absy = control.absx, control.absy
		return control.show and x >= absx and x <= absx+control.width and y >= absy and y <= absy+control.height

	def controlsAt(self, event):
		return [i for i in self.children if self.isMouseOver(event, i)]
	
	def removeAllChildren(self):
		for c in self.children: c.removeAllChildren()		
		for i in range(len(self.children)): self.children.pop()
		
class BorderedControl(Control):
	
	def __init__(self, **kwargs):
		
		Control.__init__(self, **kwargs)
		
		borderWidth = kwargs['borderWidth'] if 'borderWidth' in kwargs else DefaultControlBorderWidth
		borderColor = kwargs['borderColor'] if 'borderColor' in kwargs else DefaultControlBorderColor
		backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else DefaultControlBackground
		self.borderRenderer = kwargs['borderRenderer'] if 'borderRenderer' in kwargs else SquareBorderRenderer(self, borderColor, borderWidth, backgroundColor)
		
	def __get_br(self): return self.__border_renderer
	def __set_br(self, br): 
		self.__border_renderer = br
		self.__border_renderer.borderControl = self
	def __del_br(self): del self.__border_renderer
	borderRenderer = property(__get_br, __set_br, __del_br, "Gets/Sets the border renderer for this control")
		
	def __get_bw(self): return self.borderRenderer.borderWidth
	def __set_bw(self, bw): self.borderRenderer.borderWidth = bw
	borderWidth = property(__get_bw, __set_bw, None, "Gets/Sets the borderwidth for this control")
	
	def __get_bc(self): return self.borderRenderer.borderColor
	def __set_bc(self, bc): self.borderRenderer.borderColor = bc
	borderColor = property(__get_bc, __set_bc, None, "Gets/Sets the borderColor for this control")
	
	def __get_bgc(self): return self.borderRenderer.backgroundColor
	def __set_bgc(self, bgc): self.borderRenderer.backgroundColor = bgc
	backgroundColor = property(__get_bgc, __set_bgc, None, "Gets/Sets the backgroundColor for this control")
	
	def __repr__(self): return "Bordered Control"
		
	def renderBorder(self, surface): self.borderRenderer.render(surface)
		
	def preRender(self, surface):
		self.borderRenderer.render(surface)
			
class BorderRenderer(object):
	
	def __init__(self, borderControl=None, borderColor=DefaultControlBorderColor, borderWidth=DefaultControlBorderWidth, backgroundColor=DefaultControlBackground):
		self.borderControl = borderControl
		self.borderColor = borderColor
		self.borderWidth = borderWidth
		self.backgroundColor = backgroundColor
		
	def render(self, surface): pass
			
class SquareBorderRenderer(BorderRenderer):
	
	def render(self, surface):
		bw = self.borderWidth
		w, h = surface.get_size()
		surface.fill(self.backgroundColor, (bw, bw, w-bw, h-bw))
		bw2 = 0 if bw == 0 else int(round(float(bw)/2))
		# top
		pygame.draw.line(surface, self.borderColor, (0, 0), (w, 0), bw)
		# left
		pygame.draw.line(surface, self.borderColor, (0, 0), (0, h), bw)

		# bottom
		pygame.draw.line(surface, Control.highlightColor(self.borderColor, -70), 
						 (0, h-bw2), (w-bw2, h-bw2), bw)
		# right
		pygame.draw.line(surface, Control.highlightColor(self.borderColor, -70), 
						 (w-bw2, 0), (w-bw2, h), bw)

class RoundBorderRenderer(BorderRenderer):
	
	cornerRadius = 10
	
	def render(self, surface):
		surface.fill((0,0,0,0))
		bw = self.borderWidth
		w,h = surface.get_size()
		rect = (0,0,w,h)
		cr = self.cornerRadius
		bgc = self.backgroundColor
		bc = self.borderColor
		
		# corners (good):
		# top left
		pygame.draw.circle(surface, bgc, (cr, cr), cr); pygame.draw.circle(surface, bc, (cr, cr), cr, bw)
		# top right
		pygame.draw.circle(surface, bgc, (w-cr, cr), cr); pygame.draw.circle(surface, bc, (w-cr, cr), cr, bw)
		# bottom right
		pygame.draw.circle(surface, bgc, (w-cr, h-cr), cr); pygame.draw.circle(surface, bc, (w-cr, h-cr), cr, bw)
		# bottom left
		pygame.draw.circle(surface, bgc, (cr, h-cr), cr); pygame.draw.circle(surface, bc, (cr, h-cr), cr, bw)

		# fill
		pygame.draw.rect(surface, bgc, (cr, bw, w-cr*2, h-bw)); pygame.draw.rect(surface, bgc, (0, cr, w, h-cr*2))
		
		# lines (good)
		# top
		pygame.draw.line(surface, bc, (cr, 0), (w-cr, 0), bw)
		# right		
		pygame.draw.line(surface, bc, (w-bw, cr), (w-bw, h-cr), bw)
		# bottom
		pygame.draw.line(surface, bc, (cr, h-bw), (w-cr, h-bw), bw)
		# left
		pygame.draw.line(surface, bc, (0, cr), (0, h-cr), bw)
	
class Button(BorderedControl):
	
	def __init__(self, **kwargs):
		
		BorderedControl.__init__(self, **kwargs)
		
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else (255,255,255)
		self.callback = kwargs['callback'] if 'callback' in kwargs else None
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 24)
		self.text = kwargs['text'] if 'text' in kwargs else ''
		self.xpadding = kwargs['xpadding'] if 'xpadding' in kwargs else 12
		self.ypadding = kwargs['ypadding'] if 'ypadding' in kwargs else 8
		self.hoverColor = kwargs['hoverColor'] if 'hoverColor' in kwargs else DefaultControlHighlight

		self.width = kwargs['width'] if "width" in kwargs else self.__textBuffer.get_width() + self.xpadding
		self.height = kwargs['height'] if "height" in kwargs else self.__textBuffer.get_height() + self.ypadding
		self.borderRenderer.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else DefaultControlBackground2
		self.borderRenderer.borderColor = kwargs['borderColor'] if 'borderColor' in kwargs else DefaultControlBorderColor
		
		self.clicking = False		
		
	def __repr__(self): return "Button Control"
		
	def __get_text(self): return self.__internal_text
	def __set_text(self, txt):
		self.__internal_text = txt
		self.__textBuffer = self.font.render(self.__internal_text, True, self.fontColor)
	def __del_text(self):
		del self.__internal_text
	text = property(__get_text, __set_text, __del_text, "Text displayed on button")
	
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		
		text_x = (self.width - self.__textBuffer.get_width()) >> 1
		text_y = (self.height - self.__textBuffer.get_height()) >> 1

		surface.blit(self.__textBuffer, (text_x, text_y))
			
		if self.clicking: self.xOffset, self.yOffset = 2, 2
		else: self.xOffset, self.yOffset = 0, 0
						
	def mouseDown(self, event):
		BorderedControl.mouseDown(self, event)
		self.clicking = event.button == 1
			
	def mouseUp(self, event):
		BorderedControl.mouseUp(self, event)
		self.clicking = False
		
	def mouseEnter(self, event):
		BorderedControl.mouseEnter(self, event)
		self._origFontColor = self.fontColor
		self.fontColor = self.hoverColor
		self.text = self.text
		
	def mouseLeave(self, event):
		BorderedControl.mouseLeave(self, event)
		self.fontColor = self._origFontColor if hasattr(self, '_origFontColor') else self.fontColor	
		self.text = self.text
		
	def clicked(self, event, control):
		if self.callback and self.enabled: self.callback(event, control)
			
class Label(BorderedControl):
	"""Basic label control uses the pygame default font"""
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)

		self.borderRenderer.backgroundColor = kwargs["backgroundColor"] if "backgroundColor" in kwargs else (0,0,0,0)
				
		if "borderColor" in kwargs: 
			self.borderRenderer.borderColor = kwargs["borderColor"]
			del kwargs["borderColor"]
		else: self.borderRenderer.borderColor = (0,0,0,0)

		if "borderWidth" in kwargs: 
			self.borderRenderer.borderWidth = kwargs["borderWidth"]
			del kwargs["borderWidth"]
		else: self.borderRenderer.borderWidth = 0
		
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 24)
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else DefaultFontColor
		self.text = kwargs['text'] if 'text' in kwargs else ''
		self.xalignment = kwargs['xalignment'] if 'xalignment' in kwargs else 'left'
		self.yalignment = kwargs['yalignment'] if 'yalignment' in kwargs else 'top'
		
	def __repr__(self): return "Label Control"

	def __gettext(self): return self.__text
	def __settext(self, text):
		self.__text = text
		self.textSurface = self.font.render(self.__text, True, self.fontColor)
		if self.height < self.textSurface.get_height(): self.height = self.textSurface.get_height()
		if self.width < self.textSurface.get_width(): self.width = self.textSurface.get_width()
	def __deltext(self): del self.text		
	text = property(__gettext, __settext, __deltext, "Text displayed by Label")
	
	def __getxalign(self): return self.__xalignment
	def __setxalign(self, xalign):
		self.__xalignment = xalign
		if xalign == "left": self.__textxoffset = 0
		elif xalign == "right": 
			w = self.textSurface.get_width()
			self.__textxoffset = self.width - w
		elif xalign == "center":
			w = self.textSurface.get_width()
			self.__textxoffset = (self.width-w) >> 1
		else: self.__textxoffset = 0
	def __delxalign(self): del self.__xalignment
	xalignment = property(__getxalign, __setxalign, __delxalign, "X Alignment of text in control")

	def __getyalign(self): return self.__yalignment
	def __setyalign(self, yalign):
		self.__yalignment = yalign
		if yalign == "top": self.__textyoffset = 0
		elif yalign == "bottom": 
			h = self.textSurface.get_height()
			self.__textyoffset = self.height - h
		elif yalign == "center":
			h = self.textSurface.get_height()
			self.__textyoffset = (self.height-h) >> 1
		else: self.__textyoffset = 0
	def __delyalign(self): del self.__yalignment
	yalignment = property(__getyalign, __setyalign, __delyalign, "Y Alignment of text in control")
	
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		surface.blit(self.textSurface, (self.__textxoffset, self.__textyoffset))		

class Image(BorderedControl):
	"Display a pygame Surface object"
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		self.borderWidth = kwargs['borderWidth'] if 'borderWidth' in kwargs else 0
		self.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (0,0,0,0)
		self.surface = kwargs["surface"] if "surface" in kwargs else pygame.font.Font(None, 50).render("X", True, (150, 20, 20))

		self.width = max(self.width, self.surface.get_width())
		self.height = max(self.height, self.surface.get_height())
		
	def __repr__(self): return "Image"
		
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		x = ((self.width>>1)-(self.surface.get_width()>>1))
		y = ((self.height>>1)-(self.surface.get_height()>>1))		 
		surface.blit(self.surface, (x, y))

class ImageButton(BorderedControl):
	"""A type of button that displays an image instead of text within its borders.
	It also has an optional opacity level for its two states (hovered and not)
	"""
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		
		self.opacity = kwargs['opacity'] if 'opacity' in kwargs else 255
		self.hoverOpacity = kwargs['hoverOpacity'] if 'hoverOpacity' in kwargs else 100
		self.image = kwargs['image'] if 'image' in kwargs else pygame.font.Font(None, 50).render("X", True, (150, 20, 20))
		self.width = kwargs['width'] if 'width' in kwargs else self.image.get_width() + self.borderWidth*2
		self.height = kwargs['height'] if 'height' in kwargs else self.image.get_height() + self.borderWidth*2
		self.tmpOpacity = self.opacity
		self.clicking = False
		
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		bc = self.borderRenderer.borderColor
		bc = (bc[0], bc[1], bc[2], self.opacity)
		
		ix = ((self.width - self.image.get_width())>>1)
		iy = ((self.height - self.image.get_height())>>1)
		
		surface.blit(self.image, (ix, iy))
		
		if self.clicking: self.xOffset, self.yOffset = 2, 2
		else: self.xOffset, self.yOffset = 0, 0

	def mouseDown(self, event):
		BorderedControl.mouseDown(self, event)
		self.clicking = event.button == 1
			
	def mouseUp(self, event):
		BorderedControl.mouseUp(self, event)
		self.clicking = False
	
	def mouseEnter(self, event):
		self.tmpOpacity = self.opacity
		self.opacity = self.hoverOpacity
	
	def mouseLeave(self, event):
		self.opacity = self.tmpOpacity
		
	def clicked(self, event, control):
		if self.callback: self.callback(event, control)

class ProgressBar(BorderedControl):
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)

		self.borderRenderer.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (255,255,255,255)
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else (0,0,0)		
		self.barColor = kwargs['barColor'] if 'barColor' in kwargs else DefaultControlHighlight
		self.step = kwargs['step'] if 'step' in kwargs else 1.0
		self.max = kwargs['max'] if 'max' in kwargs else 100.0
		self.min = kwargs['min'] if 'min' in kwargs else 0.0
		self.value = kwargs['value'] if 'value' in kwargs else self.min
		self.showText = kwargs['showText'] if 'showText' in kwargs else True
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 16)
		
	def __repr__(self): return "Progress Bar"
		
	def __get_bar_color(self): return self.__bar_color
	def __set_bar_color(self, bar_color): self.__bar_color = bar_color
	def __del_bar_color(self): del self.__bar_color
	barColor = property(__get_bar_color, __set_bar_color, __del_bar_color, "The color of the progress bar")

	def __get_step(self): return self.__step
	def __set_step(self, step): self.__step = step
	def __del_step(self): del self.__step
	step = property(__get_step, __set_step, __del_step, "The increment for the progress bar")
	
	def __get_max(self): return self.__max
	def __set_max(self, max): self.__max = float(max)
	def __del_max(self): del self.__max
	max = property(__get_max, __set_max, __del_max, "The maximum value for the progress bar")
	
	def __get_min(self): return self.__min
	def __set_min(self, min): self.__min = float(min)
	def __del_min(self): del self.__min
	min = property(__get_min, __set_min, __del_min, "The minimum value for the progress bar")
	
	def __get_value(self): return self.__value
	def __set_value(self, value): 
		self.__value = float(value)
		if self.__value > self.max: self.__value = self.max
		if self.__value < self.min: self.__value = self.min
	def __del_value(self): del self.__value
	value = property(__get_value, __set_value, __del_value, "The current value for the progress bar")
	
	def __get_show_text(self): return self.__show_text
	def __set_show_text(self, show_text): self.__show_text = show_text
	def __del_show_text(self): del self.__show_text
	showText = property(__get_show_text, __set_show_text, __del_show_text, "Whether or not to display the value of the progress bar")
		
	def performStep(self): self.value += self.step
		
	def preRender(self, surface):
		BorderedControl.renderBorder(self, surface)
		internalSurface = pygame.Surface((self.width-self.borderRenderer.borderWidth*2, self.height-self.borderRenderer.borderWidth*2))
		internalSurface.fill(self.borderRenderer.backgroundColor)
		isw, ish = internalSurface.get_size()
		stepSize = float(isw-4) / (float(self.max)-float(self.min))
		width = self.value * stepSize
		pygame.draw.rect(internalSurface, self.barColor, (2, 2, width, ish-4))
		if self.showText:
			txt = self.font.render("%.0f%s" % ((self.value/self.max)*100, '%'), True, self.fontColor)
			x = (isw>>1)-(txt.get_width()>>1)
			y = (ish>>1)-(txt.get_height()>>1)
			internalSurface.blit(txt, (x,y))
		surface.blit(internalSurface, ((self.width-isw)/2, (self.height-ish)/2))
							
class TextInput(BorderedControl):
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		
		self.text = ""
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else (0,0,0)
		if 'backgroundColor' not in kwargs: self.borderRenderer.backgroundColor = (255,255,255)
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 20)
		self.width = kwargs['width'] if 'width' in kwargs else self.parent.width-20 if self.parent else 200
		self.height = self.font.get_height()+5
		
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		
		#draw text
		textSurface = self.font.render(self.text, 1, self.fontColor)		
		surface.blit(textSurface, (1, 2))
		
		#draw cursor
		w = textSurface.get_width() + 2
		pygame.draw.line(surface, self.fontColor, (w, 2), (w, self.height-3), 1)
		
	def keypress(self, event):
		tmpbuf = ""
		key = event.key
		
		if key == K_SPACE: tmpbuf = " "
		elif key == K_BACKSPACE:
			try: self.text = self.text[:-1]
			except: pass 
		else:			
			if key >= K_a and key <= K_z:
				if pygame.key.get_mods() & KMOD_SHIFT: key -= 32
				tmpbuf += chr(key)
			elif key >= K_EXCLAIM and key < K_a: tmpbuf += event.unicode
			
		if tmpbuf != '': self.text += tmpbuf
		
class ListBox(BorderedControl):
	"Unscrollable zebra control list"
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		
		self.borderRenderer.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else DefaultControlBackground
		self.xpadding = kwargs['xpadding'] if 'xpadding' in kwargs else self.borderRenderer.borderWidth
		self.ypadding = kwargs['ypadding'] if 'ypadding' in kwargs else 5
		self.oddColor = kwargs['oddColor'] if 'oddColor' in kwargs else DefaultControlBackground
		self.evenColor = kwargs['evenColor'] if 'evenColor' in kwargs else DefaultControlBackground2
		self.hoverHighlight = kwargs['hoverHighlight'] if 'hoverHighlight' in kwargs else True
		self.highlightColor = kwargs['highlightColor'] if 'highlightColor' in kwargs else DefaultControlHighlight
		
	def __repr__(self): return "ListBox"
	
	def createMouseEnterFunction(self, newControl, origControl):
		
		originalMouseEnterFunc = origControl.mouseEnter
		
		def mouseEnterFunc(event):
			originalMouseEnterFunc(event)
			if self.hoverHighlight:
				newControl.borderRenderer.originalBackgroundColor = newControl.borderRenderer.backgroundColor
				newControl.borderRenderer.backgroundColor = self.highlightColor
			
		return mouseEnterFunc
	
	def createMouseLeaveFunction(self, newControl, origControl):
		
		originalMouseLeaveFunc = origControl.mouseLeave
		
		def mouseLeaveFunc(event):
			originalMouseLeaveFunc(event)
			if self.hoverHighlight:
				try: newControl.borderRenderer.backgroundColor = newControl.borderRenderer.originalBackgroundColor
				except: pass
						
		return mouseLeaveFunc
	
	def mouseLeave(self, event):
		for c in self.children: c.mouseLeave(event)
	
	def add(self, control, sortControl=True):
		c = self.createWrapperControl(control)
		BorderedControl.add(self, c)
		if sortControl: self.sort()
		
	def createWrapperControl(self, control):
		c = BorderedControl(parent=self, borderWidth=0)
		c.x = self.xpadding
		c.width = self.width - self.xpadding*2
		c.height = control.height + self.ypadding*2
		c.borderRenderer.backgroundColor = self.evenColor if len(self.children) % 2 == 0 else self.oddColor
		c.mouseEnter = self.createMouseEnterFunction(c, control)
		c.mouseLeave = self.createMouseLeaveFunction(c, control)
		control.y = (c.height-control.height)/2
		control.x = self.xpadding
		c.add(control)
		return c
		
	def sort(self):
		y = self.borderRenderer.borderWidth
		for c in self.children:
			c.y = y
			y += c.height
					
class ScrollBox(BorderedControl): 
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		self.scroll_dy = kwargs['scroll_dy'] if 'scroll_dy' in kwargs else 8
	
	def preRender(self, surface):
		self.origClip = surface.get_clip()
		bw = self.borderRenderer.borderWidth
		surface.set_clip(bw, bw, self.width-bw*2, self.height-bw*2)
		BorderedControl.preRender(self, surface)
		
	def postRender(self, surface):
		BorderedControl.postRender(self, surface)
		surface.set_clip(self.origClip)
		
	def mouseDown(self, event):
		if event.button == 4: self.scrollUp()
		if event.button == 5: self.scrollDown()
		
	def mouseEnter(self, event):
		self.borderRenderer.borderWidth += 1

	def mouseLeave(self, event):
		self.borderRenderer.borderWidth -= 1
		
	def scrollUp(self): 
		for c in self.children: 
			c.yOffset += self.scroll_dy
			c.yOffset = min(c.yOffset, 0)
		
	def scrollDown(self): 
		for c in self.children: 
			c.yOffset -= self.scroll_dy
			c.yOffset = max(c.yOffset, -c.height)
		
class MultilineLabel(BorderedControl):
	"A label control that wraps text up to it's height (and then clips)."
	
	def __init__(self, **kwargs):
		BorderedControl.__init__(self, **kwargs)
		
		self.text = kwargs['text'] if 'text' in kwargs else None
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 24)
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else (0,0,0)
		self.borderRenderer.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (0,0,0,0)
		self.width = kwargs['width'] if 'width' in kwargs else self.getIdealSize()[0] if self.text else 0
		self.height = kwargs['height'] if 'height' in kwargs else self.getIdealSize()[1] if self.text else 0
		self.borderRenderer.borderWidth = kwargs['borderWidth'] if 'borderWidth' in kwargs else 0
		self.xpadding = kwargs['xpadding'] if 'xpadding' in kwargs else 2
		self.ypadding = kwargs['ypadding'] if 'ypadding' in kwargs else 2
	
	def __repr__(self): return "Multiline Control"

	def added(self, parent):
		self.parent = parent			
		w,h = self.getRenderedTextSize(self.text)
		self.width = max(self.width, w+self.xpadding*2)
		self.height = max(self.height, h+self.ypadding*2)

	def getIdealSize(self):
		"Returns a good width x height of the rendered text"
		lines = self.splitText(self.text)
		firstChar = lines[0][0]
		try: w, h = self.parent.width-self.borderRenderer.borderWidth*2, self.font.size(firstChar)[1] * len(lines)
		except: w, h = 1,1 
		return (w,h)
	
	def splitText(self, text):
		if not text or text == '': return []
		
		text = text.replace('\n', '  ')
		lettersPerLine = (self.width-self.borderRenderer.borderWidth*2) / (self.font.size("l")[0]*1.85) # TODO: Figure out a good way to get an accurate lettersPerLine
		spacedText = text.split(' ')
		
		# divide the spacedText into lines by line length of 40 characters
		tmp = []
		currentline = ""
		for word in spacedText:
			if word == "": tmp.append(currentline); currentline = ""
			elif len(currentline) + len(" ") + len(word) > lettersPerLine: tmp.append(currentline); currentline = word + " "
			else: currentline += word + " "
		
		tmp.append(currentline)
		return [i for i in tmp if i != ""]
	
	def getRenderedTextSize(self, text):
		
		if not text or text == "": return (0,0)		
		width, height = 0, 0		
		ty = 0
		
		for t in self.splitText(text):
			textSurface = self.font.render(t, True, (255,255,255))
			tsw = textSurface.get_width()
			width = max(width, tsw)
			ty += self.font.get_linesize()#textSurface.get_height()
		height = ty
		
		return (width,height)
		
	def renderText(self):
		w,h = self.getRenderedTextSize(self.text)
		tmpSurface = pygame.Surface((w+self.xpadding, h+self.ypadding)).convert_alpha()
		tmpSurface.fill(self.borderRenderer.backgroundColor)
		ty = self.ypadding
		for t in self.splitText(self.text):
			textSurface = self.font.render(t, True, self.fontColor)
			tmpSurface.blit(textSurface, (self.xpadding,ty))
			ty += self.font.get_linesize()
			
		return tmpSurface
			
	def preRender(self, surface):
		BorderedControl.preRender(self, surface)
		surface.blit(self.renderText(), (self.borderRenderer.borderWidth,self.borderRenderer.borderWidth))

class ChattingMultilineLabel(MultilineLabel):
	"""Does the cool "talking" text that most rpgs have. Currently breaks
	pretty badly on long texts.
	"""
	
	def __init__(self, **kwargs):
		MultilineLabel.__init__(self, **kwargs)
		self.origText = kwargs['text'] if 'text' in kwargs else ''
		self.textStart = 0
		self.textEnd = 0
		self.textPace = 1
		self.pageLength = len(self.origText)
		self.updateValue = 0
		self.chatting = True
		
	def renderText(self):
		tmpText = self.origText[self.textStart:self.textEnd]
		
		if len(tmpText) == len(self.origText): self.chatting = False
		self.text = tmpText[:self.textEnd]
		retSurface = MultilineLabel.renderText(self)
		
		self.updateValue += 1
		if self.updateValue > 1:
			self.textEnd += self.textPace
			self.updateValue = 0
			
		return retSurface

class Application(BorderedControl):
	
	def __init__(self, **kwargs):		
		BorderedControl.__init__(self, **kwargs)

		self.idleTime = kwargs['idleTime'] if 'idleTime' in kwargs else DefaultApplicationIdleTime
		self.width = kwargs['width'] if 'width' in kwargs else pygame.display.get_surface().get_width()
		self.height = kwargs['height'] if 'height' in kwargs else pygame.display.get_surface().get_height()
		self.focusedControl = None
		self.done = False
		self.buffer = None
		
	def __repr__(self): return "Application"
			
	def exit(self, button=None, event=None): self.done = True

	def run(self):
		self.buffer = pygame.Surface((self.width, self.height)).convert_alpha()
		self.buffer.fill(self.borderRenderer.backgroundColor)
		screen = pygame.display.get_surface()
		originalSurface = pygame.Surface(screen.get_size())
		originalSurface.blit(screen, (0,0))
		old_mouse = pygame.mouse.set_visible(True)
		self.done = False
		
		while not self.done:
			self.handleEvents(None)
			
			screen.blit(originalSurface, (0,0))			
			self.render(self.buffer)
			screen.blit(self.buffer, (self.x,self.y))
			self.buffer.fill(self.borderRenderer.backgroundColor)
			
			pygame.display.flip()
			pygame.time.wait(self.idleTime)
			
		pygame.mouse.set_visible(old_mouse)
		
class Dialog(Application):
	
	def __init__(self, dialogText, **kwargs):
		Application.__init__(self, **kwargs)
		
		self.width = kwargs['width'] if 'width' in kwargs else (pygame.display.get_surface().get_width()>>1)
		self.height = kwargs['height'] if 'height' in kwargs else (pygame.display.get_surface().get_height()>>1)

		if "text" in kwargs: del kwargs["text"]
		
		self.closeButton = Button(text="x", callback=self.exit)
		
		self.font = kwargs['font'] if 'font' in kwargs else pygame.font.Font(None, 32)
		self.fontColor = kwargs['fontColor'] if 'fontColor' in kwargs else (255,255,255)
		self.textLabel = MultilineLabel(parent=self, text=dialogText, font=self.font, fontColor=self.fontColor)
		self.textLabel.width = self.width - self.closeButton.width - 10
		self.textLabel.height = self.textLabel.getIdealSize()[1] + 5

		self.width = self.textLabel.width + self.closeButton.width + 10 # 5 pixel padding on each side?
		self.height = self.textLabel.height + 10 # ditto
		self.textLabel.x = 5
		self.textLabel.y = 5
		
		self.closeButton.x = self.width - self.closeButton.width
		
		self.add(self.textLabel)
		self.add(self.closeButton)
				
		self.height = max(self.height, self.textLabel.height + 10)
				
		self.center()
		
	def run(self):
		
		screen = pygame.display.get_surface()
		originalSurface = pygame.Surface(screen.get_size())
		originalSurface.blit(screen, (0,0))
		old_mouse = pygame.mouse.set_visible(True)
		
		buffer = pygame.Surface(screen.get_size()).convert_alpha()
		buffer.fill((0,0,0,0))
		self.done = False
		
		while not self.done:
			self.handleEvents(None)
			
			screen.blit(originalSurface, (0,0))
			self.render(buffer)
			screen.blit(buffer, (0,0))
			
			pygame.display.flip()
			pygame.time.wait(20)
			
		pygame.mouse.set_visible(old_mouse)
		
	def center(self):
		"""Center on the screen"""
		sw,sh = pygame.display.get_surface().get_size()
		self.x = (sw-self.width)>>1
		self.y = (sh-self.height)>>1
	   
	def keypress(self, event):
		if event.key == K_ESCAPE: self.done = True
		Application.keypress(self, event)
		
	@staticmethod
	def createOkDialog(text, **kwargs):
		okd = Dialog(text, **kwargs)
		okd.result = False		
		okd.okButton = Button(text="OK", callback=lambda x,y: (setattr(okd, 'result', True), okd.exit()), parent=okd)
		okd.height += okd.okButton.height + 10
		okd.okButton.width = 100
		okd.okButton.x = ((okd.width - okd.okButton.width)>>1)
		okd.okButton.y = okd.height - okd.okButton.height - 10				
		okd.add(okd.okButton)
		okd.keypress = lambda x: (setattr(okd, 'done', True if x.key in (K_ESCAPE, K_RETURN) else False))
		return okd
		
	@staticmethod
	def createYesNoDialog(text, **kwargs):		
		ynd = Dialog(text, **kwargs)
		ynd.result = False		
		ynd.yesButton = Button(text="Yes", callback=lambda x,y: (setattr(ynd, 'result', True), ynd.exit()), parent=ynd)
		ynd.height += ynd.yesButton.height + 10
		ynd.yesButton.width = 100
		ynd.yesButton.x = ((ynd.width - ynd.yesButton.width)>>1) - 90
		ynd.yesButton.y = ynd.height - ynd.yesButton.height - 10
		ynd.noButton = Button(text="No", callback=lambda x,y: (setattr(ynd, 'result', False), ynd.exit()), parent=ynd)
		ynd.noButton.width = 100
		ynd.noButton.x = ((ynd.width + ynd.noButton.width)>>1) - 10
		ynd.noButton.y = ynd.height - ynd.noButton.height - 10
		ynd.add(ynd.yesButton)
		ynd.add(ynd.noButton)
		
		return ynd
			
class InputDialog(Dialog):
	
	def __init__(self, text, **kwargs):
		Dialog.__init__(self, text, **kwargs)
		
		self.textLabel.height = self.textLabel.getIdealSize()[1]
		
		self.textInput = TextInput(parent=self)
		self.textInput.x = self.textLabel.x
		self.textInput.y = self.textLabel.y + self.textLabel.height + 10
		self.textInput.keypress = self.textInputKeypress
		
		self.add(self.textInput)
		self.height = 10 + self.textLabel.height + 10 + self.textInput.height + 10
		
		self.closeButton.x = self.width-self.closeButton.width
		self.result = False
		
	def textInputKeypress(self, event):
		TextInput.keypress(self.textInput, event)
		
		if event.key == K_RETURN: self.result, self.done = True, True
		elif event.key == K_ESCAPE: self.result, self.done = False, True
		
class ControlDialog(Dialog):
	
	def __init__(self, text, controls, **kwargs):
		Dialog.__init__(self, text, **kwargs)

		self.textLabel.height = self.textLabel.getIdealSize()[1]
		self.height = self.textLabel.height + 10

		dy = self.textLabel.y + self.textLabel.height + 10

		for control in controls:
			if control.width > self.width: self.width = control.width + 10
			else: control.width = self.width >> 1
			self.height += control.height + 10
			control.x = (self.width - control.width) >> 1
			control.y = dy
			dy += control.height + 10
			self.add(control)
			
		self.closeButton.x = self.width - self.closeButton.width		
		self.y = (pygame.display.get_surface().get_height() - self.height) >> 1
			
class ErrorDialog(Dialog):
	
	def __init__(self, text, **kwargs):
		Dialog.__init__(self, text, **kwargs)
		self.backgroundColor = (150,0,0)
		self.textLabel.fontColor = (255,255,255)
		self.textLabel.backgroundColor = (0,0,0,0)
			
class ProgressDialog(Dialog):
	
	def __init__(self, text, **kwargs):
		Dialog.__init__(self, text, **kwargs)
		
		self.progressBar = ProgressBar(parent=self)
		self.progressBar.width = self.width - 20
		self.progressBar.height = 20
		self.progressBar.x = (self.width-self.progressBar.width)/2
		self.progressBar.y = self.textLabel.bottom + 10
		self.height += self.progressBar.height + 20
		self.add(self.progressBar)
		
	def updateProgress(self, step):
		self.progressBar.value = self.progressBar.value + step
		
	def start(self):
		thread = threading.Thread(target=self.run)
		thread.start()
	
	def end(self):
		self.done = True
			
class ChatDialog(Dialog):
	"""Special dialog that "talks", i.e., the text appears bit by bit.
	TODO: accommodate scrolling text pauses.
	"""
	
	def __init__(self, text, **kwargs):
		Dialog.__init__(self, text, **kwargs)
		self.children.remove(self.textLabel)		
		self.textLabel = ChattingMultilineLabel(parent=self, width=self.width-self.closeButton.width-10, text=text)
		self.textLabel.x = 5
		self.textLabel.y = 5
		self.height = self.textLabel.height + 15
		self.add(self.textLabel)
		
		self.closeButton.x = self.width - self.closeButton.width
		
	def handleEvents(self, events=None):
		Dialog.handleEvents(self)
		
		keys = pygame.key.get_pressed()		
		if keys[K_SPACE]: self.textLabel.textPace = 10
		if not keys[K_SPACE]: self.textLabel.textPace = 1
		
	def keypress(self, event):
		if event.key == K_RETURN: self.done = not self.textLabel.chatting
					
class DialogBubble(BorderedControl):
	"""All the neat features of items are handled here. The size of the bubble is determined by
	its position and the location of the target control. For instance, if the target control is at
	(400,400) and the DialogBubble is at (200,200), then the size of the dialog bubble is 200x400.
	"""
	
	def __init__(self, **kwargs):		
		BorderedControl.__init__(self, **kwargs)
		self.spoutSize = kwargs['spoutSize'] if 'spoutSize' in kwargs else self.height/20
		self.spoutX = kwargs['spoutX'] if 'spoutX' in kwargs else self.width
		self.spoutY = kwargs['spoutY'] if 'spoutY' in kwargs else self.height/3+self.spoutSize
		self.cornerRadius = kwargs['cornerRadius'] if 'cornerRadius' in kwargs else 10
		self.borderRenderer = RoundBorderRenderer(self)
		self.borderRenderer.backgroundColor = kwargs['backgroundColor'] if 'backgroundColor' in kwargs else (255,255,255,255)
		self.borderRenderer.borderColor = kwargs['borderColor'] if 'borderColor' in kwargs else (0,0,0,255)
		self.borderRenderer.borderWidth = kwargs['borderWidth'] if 'borderWidth' in kwargs else 1
		self.reverseSpout = False
		self.renderSpout = True

	def __repr__(self): return "Dialog Bubble"
		
	def update(self, control):
		self.x = self.spoutX - self.width 
		self.y = self.spoutY - self.height/2
		
		if self.x < 0:
			self.x = self.spoutX+self.width
			self.spoutXrel = 0
			self.reverseSpout = True
		else:
			self.spoutXrel = self.width - self.borderRenderer.borderWidth
			
		self.spoutYrel = self.height/2
		
	def preRender(self, surface):
		"""The bubble is, in theory, supposed to look like a dialog bubble with the 
		dialog spout pointing at the target.
		"""
		bw = self.borderRenderer.borderWidth
		innerSurface = pygame.Surface((self.width-self.spoutSize-bw, self.height-bw)).convert_alpha()
		
		innerSurface.fill((0,0,0,0))
		surface.fill((0,0,0,0))
		
		self.borderRenderer.render(innerSurface)			
		
		if self.reverseSpout: surface.blit(innerSurface, (self.spoutSize, bw))
		else: surface.blit(innerSurface, (0,0))
					
		if self.renderSpout: self._renderSpout(surface, (self.spoutXrel, self.spoutYrel), self.spoutSize)
		
	def _renderSpout(self, surface, startpos, size):
		bw, x0, y0 = self.borderRenderer.borderWidth, startpos[0], startpos[1]
		
		if self.reverseSpout: x1, x2 = x0 + size + bw, x0 + size + bw
		else: x1, x2 = x0 - size - bw, x0 - size - bw
			
		y1, y2 = y0 - size - bw, y0
			
		pygame.draw.polygon(surface, self.borderRenderer.backgroundColor, [(x0,y0), (x1,y1), (x2,y2)])			
		pygame.draw.line(surface, self.borderRenderer.borderColor, (x0,y0), (x1, y1), self.borderRenderer.borderWidth)
		pygame.draw.line(surface, self.borderRenderer.borderColor, (x0,y0), (x2, y2), self.borderRenderer.borderWidth)
				
def zoomInit(control):
	control.finalWidth = control.width
	control.finalHeight = control.height
	control.steps = 15
	control.currentStep = 0
	control.widthStep = control.finalWidth / control.steps
	control.heightStep = control.finalHeight / control.steps
	control.width = 0
	control.height = 0
	control.animateInited = True
		
def zoomAnimate(control, surface):
	if not control.animateInited: return
	
	if control.width < control.finalWidth:
		control.width += control.widthStep
		
	if control.height < control.finalHeight:
		control.height += control.heightStep
		
	if control.width >= control.finalWidth and control.height >= control.finalHeight: control.animateInited = False
		
def fadeInit(control):
	control.alpha = 0
	control.steps = 100
	control.alphaStep = 255.0/control.steps
	control.borderRenderer.originalBackgroundColor = control.borderRenderer.backgroundColor
	control.animateInited = True
	
def fadeAnimate(control, surface):
	if not hasattr(control, 'animateInited'): control.animateInit(control)
	if not control.animateInited: return
	
	bg = control.borderRenderer.backgroundColor
	control.borderRenderer.backgroundColor = (bg[0], bg[1], bg[2], control.alpha)
	if hasattr(control, 'borderColor'):
		bc = control.borderRenderer.borderColor
		control.borderRenderer.borderColor = (bc[0], bc[1], bc[2], control.alpha)
	control.alpha += control.alphaStep
	
	if control.alpha >= 255: 
		control.animateInited = False;
		control.borderRenderer.backgroundColor = control.borderRenderer.originalBackgroundColor
					
if __name__ == '__main__':

	pygame.display.init()
	pygame.font.init()
	
	pygame.display.set_mode((1024,600))
	
	app = Application()
	
	bilb = Button(text="Button in ListBox", callback=lambda x,y: (sys.stdout.write("cl"), setattr(db0, 'show', not db0.show), sys.stdout.write("db0.x: %d db0.y: %d" % (db0.x, db0.y))))
	
	lb = ListBox(width=200, height=100, pos=(100,300))
	
	lb.add(Label(text="Label1"))
	lb.add(Label(text="Label2"))
	lb.add(bilb)
	lb.add(Label(text="Label4"))
	
	app.add(lb)
	
	racb = Button(text="Clear", callback=lambda x,y: lb.removeAllChildren(), pos=(lb.x, lb.bottom+10))
	app.add(racb)
	
	db0 = DialogBubble(spoutX=bilb.absx, spoutY=bilb.absy+bilb.height/2, width=200, height=200, borderWidth=2)
	db0.onTop = True
	db0.show = False
	app.add(db0)

	lbl = Label(parent=app, text="Framed:", pos=(350,200), backgroundColor=(255,0,0))
	app.add(lbl)
	rr = RoundBorderRenderer()
	box = BorderedControl(parent=app, width=300, height=300, pos=(350,220))
	box.borderRenderer = rr
	box.add(Label(text="Hi", parent=box, pos=(5,5)))
	bd = DialogBubble(borderWidth=2, spoutX=250, spoutY=200, width=200, height=300)
	bd.onTop = True
	bd.width, bd.height = 200, 200
	bd.add(Label(text="Test Bubble", pos=(5, 15)))
	#app.add(bd)
	app.add(box)

	button = Button(text="Exit")
	button.x = 10
	button.y = 10
	button.callback = lambda y,x: (x.ancestor.exit(),x)[1]  
	app.add(button)
		
	pb = ProgressBar(width=200, height=30, borderWidth=3, step=23)
	pb.x, pb.y = 10, 500
	app.add(pb)

	sb = ScrollBox(width=220, height=50, borderWidth=1, xpadding=0, ypadding=0)
	ml = MultilineLabel(parent=sb, text="This is my multiline label text that really is pretty good once you get used to it", width=200)
	sb.x = 100
	sb.y = 100
	sb.add(ml)
	app.add(sb)

	button2 = Button(text="Step PB", pos=(200,10), callback=lambda x,y: pb.performStep())
	app.add(button2)
	
	animateTest = Dialog(
"""Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Nam felis. Mauris id risus non nibh 
cursus tempus. Vestibulum lobortis velit at odio. Curabitur tortor urna, tempor sed, lobortis eu, 
porta ut, risus. Donec congue sagittis nibh. Sed rutrum venenatis turpis. Integer viverra. Aliquam 
erat volutpat. Curabitur lacinia. Nulla risus massa, molestie in, vestibulum eu, tempor a, lorem. 
Nullam cursus dapibus augue.""", backgroundColor=(100,0,0,100), fontColor=(255,255,255), animateInit=fadeInit, animateFunc=fadeAnimate)
	button3 = Button(text="Dialog", parent=app, pos=(500,10), callback=lambda x,y: animateTest.run())
	app.add(button3)
	
	button4 = Button(text="InputDialog", parent=app, pos=(500,50), callback=lambda x,y: InputDialog("Enter input:", backgroundColor=(0,100,0,200)).run())
	app.add(button4)

	button5 = Button(text="ControlDialog", parent=app, pos=(500,100), callback=lambda x,y: ControlDialog("Enter input:", [Button(text="Button"), Button(text="Number 2")], backgroundColor=(0,0,100,200)).run())
	app.add(button5)
	
	chatd = ChatDialog("This is my chat text, it isn't the best text, but it is a good text.  It might have a few quirks, but that's what we love about this text!")
	chatd.animateInit = fadeInit
	chatd.animate = fadeAnimate
	button6 = Button(text="ChatDialog", parent=app, pos=(500,150), callback=lambda x,y: chatd.run())
	app.add(button6)

	img = pygame.image.load('../data/items/default/staff/staff.png').convert_alpha()
	
	button8 = ImageButton(parent=app, pos=(660,250), image=img, width=100, height=100, borderWidth=3, backgroundColor=(250,250,250))
	button8.callback = lambda x,y: (sys.stdout.write('db.show: %s'%db.show), setattr(db, 'show', not db.show))
	app.add(button8)	

	db = DialogBubble(borderWidth=2, spoutX=button8.absx, spoutY=button8.absy+button8.height/2, width=200, height=300)
	db.onTop = True
	db.show = False
	db.width, db.height = 200, 200
	db.add(Label(text="Test Bubble", pos=(5, 15), fontColor=(0,0,0)))
	app.add(db)
	
	ic = Image(parent=app, surface=img, pos=(button5.right+10, button4.y))
	app.add(ic)
	
	app.run()
