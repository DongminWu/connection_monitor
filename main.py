
from worker import Worker
from recorder import Recorder
import multiprocessing

import config
import datetime

import os

class Controller:
    def __init__(self):
        self._config_checker()
        self.ip_addr_list = []
        self._parse_ip_addr(config.IP_ADDR_FILE)
        self.recorder =Recorder(config.LOG_PATH)
        self.msg_queue =  multiprocessing.Queue()

    def _config_checker(self):
        assert(config.LOG_PATH)
        assert(config.IP_ADDR_FILE)
        assert(config.MAX_NUM_OF_WORKERS)
        assert(config.PING_COUNT)
        assert(config.PING_SIZE)
        # assert(config.RECONNECTING_INTERVAL)


    def _parse_ip_addr(self, ip_addr_file):
        if not os.path.exists(ip_addr_file):
            raise ValueError(ip_addr_file+"doesn't exist.")

        with open(ip_addr_file, 'r') as f:
            lines = f.readlines()
            
            for l in lines:
                info = l.strip().split(',')
                if len(info) < 2:
                    continue
                print(info)
                self.ip_addr_list.append({'ip':info[0], 'name':info[1]})
    
    def _split_list(self, ori_list, number):
        '''
            split a list in to `number` lists.
            return a list of lists
        '''
        ret = []
        if len(ori_list) < number:
            ret = [[x] for x in ori_list]
        else:
            n_each, residual = divmod(len(ori_list), number)

            '''
            e.g.
            in total, 10 tasks, we want to seperate them for 4 workers
            10 divmod 4 = 2 ... 2 
            for the first 2 worker, each of them will get 2+1 jobs (3+3=6)
            for the rest of workers(4-2 = 2), they get 2+0 jobs (2+2=4)
            '''
            for idx in range(residual):
                tmp = ori_list[:n_each+1]
                ori_list = ori_list[n_each+1:]
                ret.append(tmp)
            for idx in range(number-residual):
                tmp = ori_list[:n_each]
                ori_list[n_each:]
                ret.append(tmp)
        return ret



    def do_work(self):
        print('initializing worker')
        all_task = self._split_list(self.ip_addr_list, config.MAX_NUM_OF_WORKERS)
        workers = []
        for t in all_task:
            workers.append(Worker(t, self.msg_queue))
        print('start monitoring...')
        for w in workers:
            w.start()
        while True:
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                self.recorder.write(msg, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                print(msg)

    '''
        TODO:
            1. 做个线程池的东西
            2. 把测试的跑起来
                链接controller， worker， recorder
            3. 做个gui

    '''


    
    
    

if __name__ == "__main__":
    c = Controller()
    c.do_work()
    # print(c.ip_addr_list)
    # print(c._split_list(c.ip_addr_list, 2))