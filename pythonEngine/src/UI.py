import config

from tkinter import *

def SwitchToEDITOR():
    config.EDITOR_MODE = True

window = Tk()
window.geometry('200x200')

window.title("TEST.py editor")
lbl = Label(window, text="switch to editor")
lbl.place(x=0, y=0)
btn = Button(window, text="Editor", command=SwitchToEDITOR)
btn.pack()
btn.place(x = 0, y = 30)

window.resizable(True, False)
window.mainloop()
