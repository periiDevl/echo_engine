import math
from bitstring import BitArray
from openpyxl import *

book = load_workbook('Save_001.xlsx')
sheet = book.active
book.template = False


def textToBase64(t):
     import base64

     message = t
     message_bytes = message.encode('ascii')
     base64_bytes = base64.b64encode(message_bytes)
     base64_message = base64_bytes.decode('ascii')

     return base64_message

def base64ToText(b):
     import base64
     base64_message = str(b)
     base64_bytes = base64_message.encode('ascii')
     message_bytes = base64.b64decode(base64_bytes)
     message = message_bytes.decode('ascii')
     
     return message

def SaveInfo(line, info):
     from openpyxl import Workbook
     sheet['B' + str(line)].value = textToBase64(info)
     book.save("Save_001.xlsx")

def GetInfo(line, basicInfo):
     from openpyxl import Workbook
     #checking if there is anything in that line and if there isn't replacing it with basicInfo
     if (str(sheet['B' + str(line)].value) == "None"):
          sheet['B' + str(line)].value = textToBase64(basicInfo)
          book.save("Save_001.xlsx")
          return basicInfo
     else:
          info = base64ToText(sheet['B' + str(line)].value)
          return (info)
