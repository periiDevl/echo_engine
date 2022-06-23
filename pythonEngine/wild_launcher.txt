import tkinter
from tkinter import colorchooser
import SavingSystem

global bgHex
global rbg
global fgHex
global backRColr

bgHex = SavingSystem.GetInfo(1, "#ffffff")
fgHex = SavingSystem.GetInfo(2, "#ffffff")
backRColr = SavingSystem.GetInfo(3, "#ffffff")

global root
root = tkinter.Tk()
root.resizable(False, False)
root.geometry("650x490")
root.title('wild launcher window')
root.configure(bg = backRColr)

def clickhe():
	print("Good job you clicked the button")

global r 
r = tkinter.Button(root, text="heheheha", command=clickhe, fg=fgHex, bg = bgHex)



def openStyleMenu():

	

	import tkinter
	from tkinter import colorchooser
	import SavingSystem
	global rgb
	global fgHex
	global bgHex
	
	global r
	
	st = tkinter.Tk()
	st.resizable(False, False)
	st.geometry("300x600-900+90")
	st.title('style menu')


	def bbc():
		import tkinter
		from tkinter import colorchooser
		(rgb, bgHex)= colorchooser.askcolor()
		SavingSystem.SaveInfo(1, bgHex)
		r.configure(bg = bgHex)
	bgButton = tkinter.Button(st, text="backround button color", command=bbc, fg = "Black", bg = "white", width  = 45, height = 4)
	bgButton.pack()

	def fgc():
		import tkinter
		from tkinter import colorchooser
		(rgba, fgHex)= colorchooser.askcolor()
		r['fg'] = fgHex
		SavingSystem.SaveInfo(2, fgHex)

	fgButton = tkinter.Button(st, text="text button color", command=fgc, fg = "Black", bg = "white", width  = 45, height = 4)
	fgButton.pack()

	def backroundColor():
		import tkinter
		from tkinter import colorchooser
		(y, backRColr) = colorchooser.askcolor()
		
		
		root.configure(bg = backRColr)
		SavingSystem.SaveInfo(3, str(backRColr))
	
	allbgButton = tkinter.Button(st, text="text button color", command=backroundColor, fg = "Black", bg = "white", width  = 45, height = 4)
	allbgButton.pack()
	
	canvas = tkinter.Canvas(st, width = 300, height = 600)
	canvas.create_text(100, 50, text = 'Style menu', fill = 'black')
	
	canvas.pack()

	

	SavingSystem.SaveInfo(1, bgHex)
	
	
	
	
	st.mainloop()

	



	




l = tkinter.Button(root, text="openStyleMenu", command=openStyleMenu, fg= 'Black', bg = "white")
l.pack()
r.pack()

r.place(x=175, y=100)
l.place(x=0, y=465)


root.mainloop()
