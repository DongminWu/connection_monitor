from worker import Worker, WorkerContext
import multiprocessing

import config
import datetime
import utils

import os
import time


class Controller:
    def __init__(self):
        self.view_callback = None
        self.status_callback = None


    def set_view_callback(self, callback):
        self.view_callback = callback
        return self

    def set_status_callback(self, callback):
        self.status_callback  = callback
        return self

    def _config_checker(self):
        assert(self.config["MAX_NUM_OF_WORKERS"])
        assert(self.config["PING_COUNT"])
        assert(self.config['PING_SIZE'])
        assert(self.config["PING_WAIT_TIME"])

    

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


    
    def do_work(self):
        self.status_callback('initializing worker')

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
        self.status_callback('start monitoring...')
        for w, t in self.workers:
            w.daemon = True
            w.start()
        while True:
            if self.state!= 1:
                break
            time.sleep(0.3)
            for idx in range(len(self.workers)):
                w, t = self.workers[idx]
                if not w.is_alive() and self.state == 1:
                    print('worker %s is dead, restarting' % w.pid)
                    w = Worker(t, self.context)
                    w.daemon = True
                    w.start()
                    self.workers[idx] = (w, t)
                    print('finished, new pid: %s' % w.pid)
            while not self.msg_queue.empty():
                msg = self.msg_queue.get()
                if self.view_callback:
                    self.view_callback(msg)
                print(msg)

    def terminate(self):
        self.state = -1

        for w, t in self.workers:
            print(w.pid)
            w.terminate()
        print('terminated')


    def initialize_worker(self, config, ip_addr_list):
        self.config=config
        self.ip_addr_list=ip_addr_list
        self._config_checker()
        self.msg_queue = multiprocessing.Queue()
        self.context = self._get_worker_context()
        self.workers = []
        self.state = 1

        


if __name__ == "__main__":
    c = Controller()
    c.initialize_worker(utils.load_config('./config.txt'), utils.load_ipaddr('./ipaddrs.txt'))
    c.do_work()
    # print(c.ip_addr_list)
    # print(c._split_list(c.ip_addr_list, 3))
