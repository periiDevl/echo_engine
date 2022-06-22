import math
from bitstring import BitArray

def textToBinary(t):
     b = ' '.join(format(ord(x), 'b') for x in t)
     return b

def binaryToText(b):
     # Binary string to be converted
     binary_string = b
     # split the above stirng using split() method by white space
     binary_values = binary_string.split()
     ascii_string = ""
     # use for loop to iterate
     for binary_value in binary_values:
          # convert to int using int() with base 2
          an_integer = int(binary_value, 2)
          # convert to character using chr()
          ascii_character = chr(an_integer)
          # merge them all
          ascii_string += ascii_character
     t = ascii_string
     return t

def GetCountLines(fileName):
     file = open(fileName, "r")
     line_count = 1
     for line in file:
          if line != "\n":
               line_count += 1
     return line_count

def GetLines(fileName, line):
     f = open(fileName, 'r')
     lines = f.read().splitlines()
     f.close() 
     return lines[line-1]
def SaveInfo(line, info):
     sfile = open('savefile.txt', 'a')
     sfile = open('savefile.txt', 'r')
     if sfile.mode == 'r':
          ssaveFile = sfile.readlines()
          if (GetCountLines("savefile.txt") <= line):
               ssaveFile[line] = str(textToBinary(info))
               sfile = open("savefile.txt", "w+")
               sfile.writelines(ssaveFile)
          else:
               sfile = open("savefile.txt", "w+")
               sfile.write(textToBinary(info))
          sfile.close()

def GetInfo(line, basicInfo):
     gfile = open('savefile.txt', 'a')
     gfile = open('savefile.txt', 'r')
     if gfile.mode == 'r':
          gsaveFile = gfile.readlines()
          #checking if there is anything in that line and if there isn't replacing it with basicInfo
          if (GetCountLines("savefile.txt") < line):
               gfile = open("savefile.txt", "w+")
               gfile.write(str(textToBinary(basicInfo)))
               gfile.close()
               return basicInfo
          else:
               gfile.close()
               return binaryToText(GetLines("savefile.txt", line))
