from turtle import *

t = Turtle()




def f():
    fd(20)

def b():
    bk(20)
    

def l():
    left(20)

def r():
    right(20)

onkeypress(f, "w")
onkeypress(b, "s")
onkeypress(r, "d")
onkeypress(l, "a")

listen()


