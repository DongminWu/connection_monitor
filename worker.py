
import platform
import subprocess
import multiprocessing
import os


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

    def __init__(self, addr_list, message_queue, ping_count=3, packet_size=1):
        '''
            1. pick the flag symbol in terms of the system platform.
        '''
        multiprocessing.Process.__init__(self)
        if platform.system() == "Windows":
            self.ping_count_arg = '-n'
            self.ping_size_arg = '-l'
        else:

            self.ping_count_arg = '-c'
            self.ping_size_arg = '-s'

        '''
            default values
        '''
        self.ping_count = str(ping_count)
        self.packet_size = str(packet_size)

        self.addr_list = addr_list
        self.status_list = [True] * len(addr_list)
        self.message_queue = message_queue

        '''
            2. check if the ping command is available by ping 127.0.0.1
        '''
        ret = self._ping_addr('127.0.0.1')
        if not ret:
            raise SystemError(
                "We cannot connect to 127.0.0.1, pls check your net card.")


    def run(self):
        # for i in range(1):
        # print('pid:',os.getpid(),'addr_list:', self.addr_list)
        while True:
            for idx in range(len(self.addr_list)):
                ip = self.addr_list[idx]['ip']
                name = self.addr_list[idx]['name']
                # print('pid:',os.getpid(),'ready to ping', ip)
                ret = self._ping_addr(ip)
                # print('pid:',os.getpid(),'finished ping',ip)

                if not ret :
                    # print(ip+' lost connection')
                    self.message_queue.put(':注意： '+name+'/'+ip+'断开链接')
                    self.status_list[idx] = True
                elif self.status_list[idx] and ret:
                    # print(ip+' reconnected')
                    self.message_queue.put(' '+name+'/'+ip+'已链接')
                    self.status_list[idx] = False

    def _ping_addr(self, ip_addr):
        '''
            ping an address,
            raise exception if we lost 100% packets
        '''
        # self.message_queue.put('ping ' + ip_addr )
        ret = subprocess.run(['ping', self.ping_count_arg, self.ping_count,
                              self.ping_size_arg, self.packet_size,  ip_addr], stdout=subprocess.PIPE)
        loss_rate = self._parse_ping_stdout(ret.stdout)
        if loss_rate >= 99.0:
            return False
        else:
            return True

    def _parse_ping_stdout(self, raw_text):
        if platform.system() == "Windows":
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
        {'ip':'127.0.0.1', 'name':'本机'},
        {'ip':'192.168.31.210', 'name':'平板'}
    ]
    w = Worker(fake_addr_list, fake_queue)
    # print(w._ping_addr('127.0.1.1'))
    w.start()

    while True:
        if not fake_queue.empty():
            print(fake_queue.get())
