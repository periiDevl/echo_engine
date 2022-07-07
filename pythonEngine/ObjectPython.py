from PIL import Image
import pygame
import os
import basicFunctions

class C(): pass

class Object:
### Object Info
     name = "Game Object"
     def SetName(self, _name):
          self.name = _name
     active = 1
     def SetActive(self, _active):
          self.active = _active
     thisId = 0
### Transform
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
### Sprite Renderer
     path = ""
     def SetSprite(self, _path):
          self.path = _path
     color = '#ffffff'
     def SetColor(self, _color):
          self.color = _color
     rendererlayer = 0
### Collider
     polcolliderpoints = []
     collsiondepth = 1
     def SetColDepth(self, _collisiondepth):
          self.collsiondepth = _collisiondepth
     radius = 5
     def SetColRadius(self, _Radius):
          self.radius = _Radius
     PolColOffset, CirColOffset, RectColOffset = (0,0), (0,0), (0,0)


     def SetPolColOffset(self, _Offset):
          self.PolColOffset = _Offset

     def SetCirColOffset(self, _Offset):
          self.CirColOffset = _Offset

     def SetRectColOffset(self, _Offset):
          self.RectColOffset = _Offset
     
