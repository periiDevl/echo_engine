import tkinter
import keyboard
import ObjectPython
import SceneHandler

def GetObjectByName(WantedName):
        for i in SceneHandler.SceneObjects:
                if (i.name == WantedName):
                        return i
        return SceneHandler.SceneObjects[0]

def GetObjectByID(objId):
        for i in SceneHandler.SceneObjects:
                if (i.thisId == objId):
                        return i
        return SceneHandler.SceneObjects[0]

global InspectorWin
InspectorWin = tkinter.Tk()
InspectorWin.geometry("350x1080-0+0")
InspectorWin.title("Inspector")


global InspecName
InspecBasicsText = tkinter.Label(InspectorWin, text = "BASICS", font = ('Ariel', 25), width = 15)
InspecBasicsText.pack(side=tkinter.TOP)
ObjName = tkinter.StringVar()
InspecID = 0

def ChangeObjName(Event):
        global InspecID
        print(InspecID)
        obj = GetObjectByID(InspecID)
        print(obj.name)
        obj.name = ObjName.get()
        global HeirarchyWin
        HeirarchyWin.destroy()
        HeirarchyOpen()
        return True

InspecName = tkinter.Entry(InspectorWin, text="", font = ('Ariel', 17), width = 25)
InspecName.pack(side=tkinter.TOP)
InspecName.bind('<Key-Return>', ChangeObjName)
InspecName["textvariable"] = ObjName
Active = tkinter.IntVar()
img = tkinter.PhotoImage(width=1, height=1)
InspecActive = tkinter.Checkbutton(InspectorWin, text = "Active", font = ('Ariel', 18), variable = Active, onvalue = 1, offvalue = 0)
InspecActive.pack(side=tkinter.TOP)

Ent = tkinter.Entry(InspectorWin,text="", font = ('Ariel', 15), width = 25)
Ent.pack(side=tkinter.BOTTOM)

def CheckTags():
        for i in SceneHandler.SceneObjects:
                print("Name:" + i.name + " Id:" + str(i.thisId))

def OpenInspector(Obj):
	import tkinter
	from tkinter import colorchooser
	from tkinter.messagebox import showinfo
	global InspectorWin
	global InspecName
	global InspecID
	
	InsObj = GetObjectByName(Obj)
	InspecID = InsObj.thisId
	print(InspecID)
	InspecName.delete(0,tkinter.END)
	InspecName.insert(0,Obj)
	Active.set(InsObj.active)
	return
global HeirarchyWin

def HeirarchyOpen():
	import tkinter
	from tkinter import colorchooser
	from tkinter.messagebox import showinfo
	import SavingSystem
	global HeirarchyWin
	HeirarchyWin = tkinter.Tk()
	HeirarchyWin.geometry("350x1080+0+0")
	HeirarchyWin.title("Heirarchy")
	def item_selected(event):
		selected_indice = HierarchyList.curselection()
		
		selected_lang= ",".join([HierarchyList.get(i) for i in selected_indice])
		msg = f'You selected: {selected_lang}'

		if (selected_lang != ""):
			OpenInspector(selected_lang)

        				    
	L = tkinter.Label(HeirarchyWin, text ="Hierarchy",width = 35, height = 69)
	L.pack()
	
	HierarchyList = tkinter.Listbox(L, height = HeirarchyWin.winfo_screenheight(), width = int(HeirarchyWin.winfo_reqwidth()))
	for obj in SceneHandler.SceneObjects:
		HierarchyList.insert(obj.layer, obj.name)
	
	HierarchyList.bind('<<ListboxSelect>>', item_selected) 
	HierarchyList.pack(fill="both")
	
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
  
tkinter.mainloop()
