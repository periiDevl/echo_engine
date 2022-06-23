import tkinter
import keyboard
Screen = tkinter.Tk()
Screen.geometry("1920x1080")

def OpenInspector(Object):
	import tkinter
	from tkinter import colorchooser
	from tkinter.messagebox import showinfo
	InspectorLabel = tkinter.Label(Screen, text ="",bg = "White" ,width = 45, height = 69)
	InspectorLabel.pack()
	InspectorLabel.place(x=Screen.winfo_screenwidth()-(45*7), y=0)


def HeirarchyOpen():
	import tkinter
	from tkinter import colorchooser
	from tkinter.messagebox import showinfo
	import SavingSystem

	global HierarchyList	
	
	def items_selected(event):
		selected_indices = HierarchyList.curselection()
		
		selected_langs = ",".join([HierarchyList.get(i) for i in selected_indices])
		msg = f'You selected: {selected_langs}'

		OpenInspector(selected_langs)
		
				    
	L = tkinter.Label(Screen, text ="Hierarchy",width = 35, height = 69)
	L.pack()
	L.place(x=0, y=0)
	
	HierarchyList = tkinter.Listbox(L, height = Screen.winfo_screenheight(), width = 45)
	HierarchyList.insert(0, 'Player')
	HierarchyList.insert(1, 'Enemy')
	HierarchyList.insert(1, 'there is so much text going on')
	HierarchyList.bind('<<ListboxSelect>>', items_selected) 
	HierarchyList.pack(fill="both")
	#HierarchyList.place(x=0, y=75)

	
HeirarchyOpen()

def OpenMenu():
	m = tkinter.Menu(Screen, tearoff = 0)
	m.add_command(label ="Cut")
	m.add_command(label ="Copy")
	m.add_command(label ="Paste")
	m.add_command(label ="Reload")
	m.add_separator()
	m.add_command(label ="Rename")

def do_popup(event):
    try:
        m.tk_popup(event.x_root, event.y_root)
    finally:
        m.grab_release()
  
Screen.mainloop()
