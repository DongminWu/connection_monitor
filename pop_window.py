from tkinter import Tk, messagebox
import sys

root = Tk()
root.withdraw()
messagebox.showwarning(title='warning', message=sys.argv[1])