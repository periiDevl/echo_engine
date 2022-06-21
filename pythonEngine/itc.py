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


#onkeypress(f, "w")
#onkeypress(b, "s")
#onkeypress(r, "d")
#onkeypress(l, "a")
#listen()

turY = t.ycor()
turT = t.xcor()

bx = 5
by = 5

fd(10)

if (turY > by or turT > bx):
	right(40)
	print("onBound")
	





