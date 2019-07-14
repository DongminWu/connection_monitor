from tkinter import *

import time
import threading
import utils
from controller import Controller
from recorder import Recorder
import datetime
import multiprocessing


class ListView:
    def __init__(self, parent, name):
        self.view_name = name
        self.parent = parent
        self.limit = -1
        self.my_recoder = None

    def build(self):
        self.history_frame = LabelFrame(self.parent, text=self.view_name)
        self.scroll = Scrollbar(self.history_frame)
        self.scroll.pack(side=RIGHT, fill=Y)
        self.list_box = Listbox(
            self.history_frame, selectmode=SINGLE, yscrollcommand=self.scroll.set)
        self.list_box.pack(side=LEFT, fill=BOTH, expand=1)
        self.scroll.config(command=self.list_box.yview)
        self.list_box.see(END)
        return self.history_frame

    def set_limit(self, num):
        self.limit = num
        return self

    def append(self, msg):
        '''
            msg = string
        '''
        if self.limit > 0:
            if self.list_box.size() >= self.limit:
                self.list_box.delete(0)
        self.list_box.insert(END, msg)
        self.list_box.see(END)
        return self

    def update(self, index, msg):
        if index < self.list_box.size():
            self.list_box.delete(index)
            self.list_box.insert(index, msg)

    def set_default_color(self, index):
        self.list_box.itemconfig(
            END, {'bg': 'SystemButtonFace', 'fg': 'SystemButtonFace'})
        return self

    def set_green(self, index):
        self.list_box.itemconfig(index, {'bg': 'green', 'fg': 'black'})
        return self

    def set_red(self, index):
        self.list_box.itemconfig(index, {'bg': 'red', 'fg': 'white'})
        return self

    def clean(self):
        self.list_box.delete(0, END)
        return self


class InputBox:
    def __init__(self, parent, name):
        self.tag_name = name
        self.parent = parent

    def build(self):
        self.frame = Frame(self.parent)
        self.tag = Label(self.frame, text=self.tag_name)
        self.entry = Entry(self.frame)
        self.tag.pack(side=LEFT)
        self.entry.pack(side=RIGHT, fill=X, expand=1)
        return self.frame

    def set_text(self, text):
        self.entry.delete(0, END)
        self.entry.insert(0, text)

    def get_text(self):
        return self.entry.get()

    def enable(self):
        self.entry.config(state=NORMAL)

    def disable(self):
        self.entry.config(state=DISABLED)


class MainView(Tk):
    def __init__(self):
        super().__init__()
        self.initialize_view()
        self.controller = Controller()
        self.controller.set_view(self)

        self.working_t = None
        self.recorder = None
        

    def initialize_view(self):
        self.title("auto ping")
        self.status_list = ListView(self, '链接状态')

        self.status_list.build().grid(column=0, row=0, sticky=NSEW,
                                      padx=10, pady=10, columnspan=2)

        self.start_button = Button(self, text='start', padx=5,
                                   pady=5, relief=RIDGE, command=self.on_press_startbutton)
        self.stop_button = Button(self, text='stop', padx=5,
                                  pady=5, relief=FLAT, command=self.on_press_stopbutton)

        self.ipaddr_file_box = InputBox(self, 'IP地址文件:    ')
        self.log_folder_box = InputBox(self,  '日志存储路径:')

        self.ipaddr_file_box.build().grid(row=1, columnspan=2, sticky=E+W, padx=10)
        self.log_folder_box.build().grid(row=2, columnspan=2, sticky=E+W, padx=10)

        self.ipaddr_file_box.set_text('./ipaddrs.txt')
        self.log_folder_box.set_text('./save')

        self.start_button.grid(column=0, row=3, padx=10, pady=10, sticky=NSEW)
        self.stop_button.grid(column=1, row=3, padx=10, pady=10, sticky=NSEW)

        self.status_msg = StringVar()
        self.status_msg.set('欢迎！')
        self.status_bar = Label(self, textvariable=self.status_msg)
        self.status_bar.grid(row=4, sticky=E+W, columnspan=2)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def on_press_startbutton(self):

        self.ipaddr_file_box.disable()
        self.log_folder_box.disable()
        self.status_list.clean()

        # 1. hard code config
        # 2. add count in config
        # 3. controller.daemon = False
        config = {
            "MAX_NUM_OF_WORKERS": 4,
            "PING_COUNT": 1,
            'PING_SIZE': 1,
            'PING_WAIT_TIME': 20,
            'WORK_COUNT': 1000
        }
        ipaddr_list = utils.load_ipaddr(self.ipaddr_file_box.get_text())
        self.my_recoder = Recorder(self.log_folder_box.get_text())
        self.controller.initialize_worker(config, ipaddr_list, recorder=self.my_recoder)
        self.controller.daemon = False
        self.working_t = threading.Thread(target=self.controller.do_work)
        self.working_t.start()

    def on_press_stopbutton(self):
        print('terminating')
        self.controller.terminate()
            

    def do_work(self):
        self.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    a = MainView()
    a.geometry('600x500')
    a.do_work()
    print('作者：吴东民，邮箱：wdm228@126.com')
