from worker import Worker, WorkerContext
import multiprocessing

import config
import datetime
import utils

import os
import time


class Controller:
    def __init__(self):
        self.callback = None
        self.config = {}
        self.ip_addr_list = []

    def set_callback(self, callback):
        self.callback = callback
        return self

    def _config_checker(self):
        assert(self.config["MAX_NUM_OF_WORKERS"])
        assert(self.config["PING_COUNT"])
        assert(self.config['PING_SIZE'])
        assert(self.config["PING_WAIT_TIME"])

    def _parse_txt(self, ip_addr_file):
        ret = []
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
                ret.append(info)
        return ret

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
        context.set_ping_count(self.config["PING_COUNT"])
        context.set_ping_size(self.config['PING_SIZE'])
        context.set_ping_wait_time(self.config["PING_WAIT_TIME"])
        if not context.message_queue:
            raise ValueError('the message queue should not be None..')
        print('ping command:', ' '.join(
            context.generate_ping_command('127.0.0.1')))
        return context
    def load_config(self, path):
        res = self._parse_txt(path)
        for each in res:
            self.config[each[0]] = int(each[1])
        print(self.config)
        return self
        
    def load_ipaddr(self, path):
        res = self._parse_txt(path)
        for each in res:
            self.ip_addr_list.append({'ip':each[0], 'name':each[1]})
        print(self.ip_addr_list)
        return self
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
            self.ip_addr_list, self.config["MAX_NUM_OF_WORKERS"])
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
                if self.callback:
                    self.callback(msg)
                print(msg)
        print('monitoring terminated')

    def terminate(self):
        self.status = -1

        for w, t in self.workers:
            w.terminate()

    def initialize_worker(self):
        self._config_checker()
        self.msg_queue = multiprocessing.Queue()
        self.context = self._get_worker_context()
        self.workers = []
        self.status = 0
        


if __name__ == "__main__":
    c = Controller()
    c.load_config('./config.txt')
    c.load_ipaddr('./ipaddrs.txt')
    c.initialize_worker()
    c.do_work()
    # print(c.ip_addr_list)
    # print(c._split_list(c.ip_addr_list, 3))
