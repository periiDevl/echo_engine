from PIL import Image
import pygame
import basicFunctions

class C(): pass

class Object:
     name = ""
     active = 1
     thisId = 0
     def __init__(self):
          self.thisId = id(self)
     class transform:
          position = (0,0)
          rotation = (0)
          scale = (1,1)
          def SetPos(self, position):
               self.position = position
     class spriteRen:
          sprite = pygame.image.load("Empty.png")
          color = (255, 255, 255, 255)
