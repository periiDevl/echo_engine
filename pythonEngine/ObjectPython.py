from PIL import Image
import pygame
import os
import basicFunctions

class C(): pass

class Object:
     name = "Game Object"
     def SetName(self, _name):
          self.name = _name
     active = 1
     def SetActive(self, _active):
          self.active = _active
     thisId = 0
          
     def __init__(self):
          self.thisId = id(self)
     position = pygame.Vector2(int(0), int(0))
     def SetPos(self, _pos):
          self.position = _pos
     rotation = 0
     def SetRot(self, _rot):
          self.rotation = _rot
     scale = pygame.Vector2(1, 1)
     def SetScale(self, _scale):
          self.scale = _scale
     drag = False

     path = ""
     def SetSprite(self, _path):
          self.path = _path
     color = '#ffffff'
     def SetColor(self, _color):
          self.color = _color
     layer = 0