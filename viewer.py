from tkinter import *

import time
import threading

'''
class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title = 'test'
        self.var_to_change = tkinter.StringVar()
        self.var_to_change.set('hello')
        self.label = tkinter.Label(self, textvariable=self.var_to_change)
        self.label.grid(column=0, row=0)

    def test_thread(self):
        time.sleep(1)
        self.var_to_change.set('bye')

    def lets_go(self):
        t = threading.Thread(target=self.test_thread, name='thread-1')
        t.start()
        self.mainloop()

if __name__ == "__main__":
    top = App()
    top.lets_go()
'''

class MainView(Tk):
    def __init__(self):
        super().__init__()
        self.title = "auto ping"


        
        self.frame = LabelFrame(self, text="历史记录", width=200, height=200)
        self.frame.pack()
        self.scroll = Scrollbar(self.frame)
        self.scroll.pack(side=RIGHT,fill=Y)
        self.list_box = Listbox(self.frame, selectmode=SINGLE, yscrollcommand=self.scroll.set)
        for i in range(20):
            self.list_box.insert(END, str(i)+": yo")
        a = self.list_box.get(12)
        print(a)
        self.list_box.pack(side=LEFT, fill=BOTH)
        self.scroll.config(command=self.list_box.yview)
        self.list_box.see(END) 
        
    def get_log_screen(self):
        pass
    def get_start_button(self):
        pass
    
    def get_status_screen(self):
        pass

    def get_alert_box(self):
        pass  

    def test_thread(self):
        time.sleep(2)
        self.list_box.see(END)
    def lets_go(self):
        def test_callback(event):
            print(event.type)
        t = threading.Thread(target=self.test_thread)
        t.start()
        self.scroll.bind("<ButtonRelease>", test_callback)
        self.scroll.bind("<Button-1>", test_callback)
        self.scroll.bind("<Leave>", test_callback)
        self.scroll.bind("<Enter>", test_callback)



        self.mainloop()


if __name__ == "__main__":
    a = MainView()
    
    a.lets_go()