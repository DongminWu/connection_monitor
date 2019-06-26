
from worker import Worker, WorkerContext
from recorder import Recorder
import multiprocessing

import config
import datetime
import utils

import os
import time


class Controller:
    def __init__(self):
        self.initialize()

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
        with open(ip_addr_file, 'rb') as f:
            lines = f.readlines()

            for l in lines:

                try:
                    l = l.decode('utf-8')
                except UnicodeDecodeError:
                    l = l.decode('gbk')
                
                info = l.strip().split(',')
                if len(info) < 2:
                    continue
                print(info)
                self.ip_addr_list.append({'ip': info[0], 'name': info[1]})

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
                ori_list = ori_list[n_each:]
                ret.append(tmp)
        return ret

    def _get_worker_context(self):
        context = WorkerContext()
        context.set_msg_queue(self.msg_queue)
        context.set_ping_count(config.PING_COUNT)
        context.set_ping_size(config.PING_SIZE)
        context.set_ping_wait_time(config.PINT_WAIT_TIME)
        if not context.message_queue:
            raise ValueError('the message queue should not be None..')
        print('ping command:', ' '.join(context.generate_ping_command('127.0.0.1')))
        return context
        

    def do_work(self):
        self.status = 1
        print('initializing worker')

        # test the net card and ping
        test_worker = Worker(['127.0.0.1'], self.context)
        ret = test_worker.is_workable()
        if not ret:
            raise SystemError(
                "We cannot connect to 127.0.0.1, pls check your net card.")

        all_task = self._split_list(
            self.ip_addr_list, config.MAX_NUM_OF_WORKERS)
        self.workers = []
        for t in all_task:
            self.workers.append((Worker(t, self.context), t))
        print('start monitoring...')
        for w, t in self.workers:
            w.daemon = True
            w.start()
        while self.status == 1:
            time.sleep(0.3)
            for idx in range(len(self.workers)):
                w, t = self.workers[idx]
                if not w.is_alive():
                    print('worker %s is dead, restarting' % w.pid)
                    w = Worker(t, self.context)
                    w.daemon = True
                    w.start()
                    self.workers[idx] = (w, t)
                    print('finished, new pid: %s' % w.pid)
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                self.recorder.write(
                    str(msg), datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                print(msg)
    def terminate(self):
        self.status = -1
        for w, t in self.workers:
            w.terminate()
        
        del self.msg_queue
        del self.context
        

    def initialize(self):
        self._config_checker()
        self.ip_addr_list = []
        self._parse_ip_addr(config.IP_ADDR_FILE)
        self.recorder = Recorder(config.LOG_PATH)
        self.msg_queue = multiprocessing.Queue()
        self.context = self._get_worker_context()
        self.workers = []
        self.status = 0
        

if __name__ == "__main__":
    c = Controller()
    c.do_work()
    # print(c.ip_addr_list)
    # print(c._split_list(c.ip_addr_list, 3))
