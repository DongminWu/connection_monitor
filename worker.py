import subprocess
import multiprocessing
import os

import utils

import time


class WorkerContext:
    def __init__(self):
        self.message_queue = None
        self.ping_count = 1
        self.ping_size = 1
        self.ping_wait_time = 1
        if utils.is_windows():
            self.ping_count_arg = '-n'
            self.ping_size_arg = '-l'
            self.ping_wait_time_arg = "-w"
        else:

            self.ping_count_arg = '-c'
            self.ping_size_arg = '-s'
            self.ping_wait_time_arg = '-W'

    def set_msg_queue(self, queue):
        self.message_queue = queue
        return self

    def set_ping_count(self, count):
        self.ping_count = count
        return self

    def set_ping_size(self, size):
        self.ping_size = size
        return self

    def set_ping_wait_time(self, second):
        self.ping_wait_time = second
        return self

    def generate_ping_command(self, ip_addr):
        ret = ['ping']
        ret.append(self.ping_count_arg)
        ret.append(str(self.ping_count))
        ret.append(self.ping_size_arg)
        ret.append(str(self.ping_size))
        ret.append(self.ping_wait_time_arg)
        ret.append(str(int(self.ping_wait_time)))
        ret.append(ip_addr)
        return ret


class Worker(multiprocessing.Process):

    '''
        NOTE:
        structure of `addr_list`:
            [
                {
                    'ip': '127.0.0.1,
                    'name': 哟哟哟
                }
                ,....
            ]
    '''

    def __init__(self, addr_list, context):
        '''
            1. pick the flag symbol in terms of the system platform.
        '''
        multiprocessing.Process.__init__(self)
        self.context = context
        self.addr_list = addr_list
        self.status_list = [utils.MSG_STATUS.invalid] * len(addr_list)
        self.state = True

        self.message_queue = self.context.message_queue
        if not self.message_queue:
            raise ValueError('we need a message queue')

        '''
            2. check if the ping command is available by ping 127.0.0.1
        '''

    def run(self):
        # for i in range(1):
        print('pid:',os.getpid(),'is running')
        while True:
            time.sleep(0.1)
            for idx in range(len(self.addr_list)):
                ip = self.addr_list[idx]['ip']
                name = self.addr_list[idx]['name']
                ret = self._ping_addr(ip)

                if not ret and self.status_list[idx] != utils.MSG_STATUS.disconnected:
                    # print(ip+' lost connection')
                    self.message_queue.put(
                        utils.MessagePacket(ip, name, utils.MSG_STATUS.disconnected))
                    self.status_list[idx] = True
                elif self.status_list[idx] and self.status_list[idx] != utils.MSG_STATUS.reconnected:
                    # print(ip+' reconnected')
                    self.message_queue.put(
                        utils.MessagePacket(ip, name, utils.MSG_STATUS.reconnected))
                    self.status_list[idx] = False
        print('pid:',os.getpid(),'terminated')
        

    def is_workable(self):
        for each in self.addr_list:
            r = self._ping_addr(each)
            if not r:
                return False
        return True

    def _ping_addr(self, ip_addr):
        '''
            ping an address,
            raise exception if we lost 100% packets
        '''
        # self.message_queue.put('ping ' + ip_addr )
        ret = subprocess.run(
            self.context.generate_ping_command(ip_addr), stdout=subprocess.PIPE)
        loss_rate = self._parse_ping_stdout(ret.stdout)
        if loss_rate >= 99.0:
            return False
        else:
            return True

    def _parse_ping_stdout(self, raw_text):
        if utils.is_windows():
            raw_text = raw_text.decode('gbk')
            end = -1
            begin = -1
            for e in raw_text.splitlines():
                if e.find('无法访问目标主机') != -1:
                    break
                end = e.find('%')
                if end != -1:
                    begin = e.rfind('(')
                    last_line = e
                    break
            if begin + 1 >= end:
                loss_rate = 100.0
            else:
                loss_rate = float(last_line[begin+1:end].strip())
            # print('loss_rate=', loss_rate)
        else:
            raw_text = raw_text.decode('utf-8')
            last_line = raw_text.splitlines()[-1]
            end = last_line.find('%')
            begin = last_line.rfind(',')
            if begin + 1 >= end:
                loss_rate = 100.0
            else:
                loss_rate = float(last_line[begin+1:end].strip())
        return loss_rate


if __name__ == "__main__":

    fake_queue = multiprocessing.Queue()
    fake_addr_list = [
        {'ip': '127.0.0.1', 'name': '本机'},
        {'ip': '192.168.31.210', 'name': '平板'}
    ]

    fake_context = WorkerContext()
    fake_context.set_msg_queue(fake_queue)
    fake_context.set_ping_count(3)
    fake_context.set_ping_size(1)
    fake_context.set_ping_wait_time(1)

    w = Worker(fake_addr_list, fake_context)
    # print(w._ping_addr('127.0.1.1'))
    w.start()

    while True:
        if not fake_queue.empty():
            print(fake_queue.get())
