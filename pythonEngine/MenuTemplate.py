import tkinter
Screen = tkinter.Tk()
Screen.geometry("1920x1080")

L = tkinter.Label(Screen, text ="Right-click to display menu",width = 40, height = 20)
L.pack()

m = tkinter.Menu(Screen, tearoff = 0)
m.add_command(label ="Destroy")
m.add_command(label ="Repair")
m.add_command(label ="Eat shit")
m.add_command(label ="Joke")
m.add_separator()
m.add_command(label ="Summon mouse")

def do_popup(event):
    try:
        m.tk_popup(event.x_root, event.y_root)
    finally:
        m.grab_release()
  
L.bind("<Button-3>", do_popup)

Screen.mainloop()
