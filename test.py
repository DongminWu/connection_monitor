from tkinter import *

top = Tk()

e = Entry(top)
e.pack()

e.delete(0, END)
e.insert(0, "a default value")
e.insert(1, 'yyooyo')
e.config(state=DISABLED)
top.mainloop()