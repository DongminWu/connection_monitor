from tkinter import *

import time
import threading
import utils
from controller import Controller
from recorder import Recorder
import datetime
import multiprocessing

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
        self.limit = -1

    def build(self):
        self.history_frame = LabelFrame(self.parent, text=self.view_name)
        self.scroll = Scrollbar(self.history_frame)
        self.scroll.pack(side=RIGHT, fill=Y, expand=1)
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
        self.controller.set_view_callback(self.view_callback)
        self.controller.set_status_callback(self.status_callback)

        self.working_t = None
        self.recorder = None
        self.ipaddr_to_status = {}

    def initialize_view(self):
        self.title("auto ping")
        self.history_list = ListView(self, '历史记录')
        self.status_list = ListView(self, '链接状态')

        self.history_list.build().grid(column=0, row=0, padx=10, pady=10)
        self.status_list.build().grid(column=1, row=0, padx=10, pady=10)

        self.start_button = Button(self, text='start', padx=5,
                                   pady=5, relief=RIDGE, command=self.on_press_startbutton)
        self.stop_button = Button(self, text='stop', padx=5,
                                  pady=5, relief=FLAT, command=self.on_press_stopbutton)

        self.config_file_box = InputBox(self, '配置文件地址:')
        self.ipaddr_file_box = InputBox(self, 'IP地址文件:    ')
        self.log_folder_box = InputBox(self,  '日志存储路径:')

        self.config_file_box.build().grid(row=1, columnspan=2, sticky=NSEW, padx=10)
        self.ipaddr_file_box.build().grid(row=2, columnspan=2, sticky=NSEW, padx=10)
        self.log_folder_box.build().grid(row=3, columnspan=2, sticky=NSEW, padx=10)

        self.config_file_box.set_text('./config.txt')
        self.ipaddr_file_box.set_text('./ipaddrs.txt')
        self.log_folder_box.set_text('./save')

        self.start_button.grid(column=0, row=4, padx=10, pady=10)
        self.stop_button.grid(column=1, row=4, padx=10, pady=10)

        self.status_msg = StringVar()
        self.status_msg.set('欢迎！')
        self.status_bar = Label(self, textvariable=self.status_msg)
        self.status_bar.grid(row=5)

    def view_callback(self, msg):
        self.history_list.append(str(msg))
        self.recorder.write(str(msg), datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
        self.ipaddr_to_status[msg.ip]['status'] = msg.status
        
        if msg.status == utils.MSG_STATUS.disconnected:
            self.status_list.set_red(self.ipaddr_to_status[msg.ip]['index'])
        elif msg.status == utils.MSG_STATUS.reconnected:
            self.status_list.set_green(self.ipaddr_to_status[msg.ip]['index'])

        print(self.ipaddr_to_status[msg.ip]['index'], msg)


    def status_callback(self, msg):
        self.status_msg.set(msg)

    def on_press_startbutton(self):
        if not self.working_t:

            self.config_file_box.disable()
            self.ipaddr_file_box.disable()
            self.log_folder_box.disable()

            config = utils.load_config(self.config_file_box.get_text())
            ipaddr_list = utils.load_ipaddr(self.ipaddr_file_box.get_text())
            self.recorder = Recorder(self.log_folder_box.get_text())

            for idx in range(len(ipaddr_list)):
                self.status_list.append("%s(%s)" % (ipaddr_list[idx]['name'], ipaddr_list[idx]['ip']))
                self.status_list.set_red(idx)

                self.ipaddr_to_status[ipaddr_list[idx]['ip']] = {
                    'name': ipaddr_list[idx]['name'], 
                    'status': utils.MSG_STATUS.disconnected,
                    'index': idx
                    }

            print(self.ipaddr_to_status)
            self.controller.initialize_worker(config, ipaddr_list)
            self.working_t = threading.Thread(target=self.controller.do_work)
            self.working_t.start()

    def on_press_stopbutton(self):
        if self.working_t:
            self.controller.terminate()
            self.working_t.join()
            self.status_msg.set('监控停止')
            self.working_t = None
            self.history_list.clean()
            self.status_list.clean()
            self.config_file_box.enable()
            self.ipaddr_file_box.enable()
            self.log_folder_box.enable()

    def do_work(self):
        self.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    a = MainView()
    a.resizable(width=False, height=False)
    a.do_work()
