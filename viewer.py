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


class ListView:
    def __init__(self, parent, name):
        self.view_name = name
        self.parent = parent

    def build(self):
        self.history_frame = LabelFrame(self.parent, text=self.view_name)
        self.scroll = Scrollbar(self.history_frame)
        self.scroll.pack(side=RIGHT, fill=Y, expand=1)
        self.list_box = Listbox(
            self.history_frame, selectmode=SINGLE, yscrollcommand=self.scroll.set)
        for i in range(20):
            self.list_box.insert(END, str(i)+": yo")
        self.list_box.itemconfig(1, {'bg': 'red', 'fg': 'white'})
        self.list_box.pack(side=LEFT, fill=BOTH, expand=1)
        self.scroll.config(command=self.list_box.yview)
        self.list_box.see(END)
        return self.history_frame


class MainView(Tk):
    def __init__(self):
        super().__init__()
        self.title("auto ping")
        history_list = ListView(self, '历史记录').build()
        status_list = ListView(self, '链接状态').build()

        history_list.grid(column=0, row=0, padx = 10, pady=10)
        status_list.grid(column=1, row=0, padx = 10, pady=10)

        start_button = Button(self, text='start', padx=5,
                              pady=5, relief=RIDGE, command=self.on_press_startbutton)
        stop_button = Button(self, text='stop', padx=5,
                             pady=5, relief=FLAT, command=self.on_press_stopbutton)

        start_button.grid(column=0, row=1, padx = 10, pady=10)
        stop_button.grid(column=1, row=1, padx = 10, pady=10)

        status_msg = StringVar()
        status_msg.set('yoyo阿斯顿发送到发送到发送到蒂芬y')
        status_bar = Label(self, textvariable=status_msg)
        status_bar.grid(row=2)

    def on_press_startbutton(self):
        print('start_button')

    def on_press_stopbutton(self):
        print('stop_button')

    def get_alert_box(self):
        pass


if __name__ == "__main__":
    a = MainView()
    a.resizable(width=False, height=False)
    a.mainloop()
