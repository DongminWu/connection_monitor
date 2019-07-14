from worker import Worker, WorkerContext
from recorder import Recorder
import multiprocessing
from tkinter import *
import datetime
import utils

import os
import time

from copy import deepcopy


class Controller:
    def __init__(self):
        self.status_callback = None
        self.daemon = True
        self.view = None

    def set_status_callback(self, callback):
        self.status_callback = callback
        return self

    def set_view(self, view_obj):
        self.view = view_obj
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
        if self.config['WORK_COUNT']:
            context.set_work_count(self.config['WORK_COUNT'])
        if not context.message_queue:
            raise ValueError('the message queue should not be None..')
        print('ping command:', ' '.join(
            context.generate_ping_command('127.0.0.1')))
        return context

    def do_work(self):
        self.view.status_msg.set('initializing worker')
        self.view.start_button.config(state=DISABLED)
        self.recorder.write('************started @ %s*****************'
                            % datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))

        # test the net card and ping
        test_context = WorkerContext()
        test_context.set_msg_queue(self.msg_queue)
        test_context.set_work_count(1)
        test_worker = Worker([{'ip': '127.0.0.1', 'name': 'test',
                               'status': utils.MSG_STATUS.disconnected}], test_context)
        test_worker.start()
        test_worker.join()
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
        ret = (msg.status == utils.MSG_STATUS.reconnected)
        if not ret:
            raise SystemError(
                "We cannot connect to 127.0.0.1, pls check your net card.")

        all_task = self._split_list(
            self.ip_addr_list, self.config["MAX_NUM_OF_WORKERS"])
        self.workers = []
        for t in all_task:
            self.workers.append((Worker(t, self.context), t))
        self.view.status_msg.set('start monitoring...')
        for w, t in self.workers:
            w.daemon = True
            w.start()
        while True:
            if self.state == 1:
                # time.sleep(0.3)
                is_all_worker_dead = True
                for idx in range(len(self.workers)):
                    w, t = self.workers[idx]
                    if not w.is_alive() and self.state == 1 and self.daemon == True:
                        print('worker %s is dead, restarting' % w.pid)
                        w = Worker(t, self.context)
                        w.daemon = True
                        w.start()
                        self.workers[idx] = (w, t)
                        print('finished, new pid: %s' % w.pid)
                    # if all worker finished their job, return
                    if not self.daemon:
                        if w.is_alive():
                            is_all_worker_dead = False
                            break
                msg = self.msg_queue.get()
                self.view_callback(msg)
                if is_all_worker_dead:
                    print('no one alive')
                    self.state = -1

            if self.state == -1:
                print('terminating...')
                all_dead = False
                while not all_dead:
                    all_dead = True
                    for w, t in self.workers:
                        if w.is_alive():
                            w.terminate()
                            print('sent terminate to', w.pid)
                            all_dead = False
                # dump all messages
                while not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    self.view_callback(msg)
                self.view.ipaddr_file_box.enable()
                self.view.log_folder_box.enable()
                self.view.start_button.config(state=NORMAL)
                self.record_statistics()

                self.recorder.write('************ended @ %s*****************'
                                    % datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))

                break

        print('controller returned with state:', self.state)

        # after work

    def terminate(self):
        self.state = -1

    def record_statistics(self):
        print(self.ipaddr_to_status)
        if self.recorder:
            self.recorder.write('已测试%d个IP地址' % len(self.ipaddr_to_status))
            for k, v in self.ipaddr_to_status.items():
                loss_rate = 100 * v['loss_count'] / v['total_count']
                log = "%s(%s) 丢包率:%d%%" % (v['name'], k, loss_rate)
                self.recorder.write(log)

    def initialize_worker(self, config, ip_addr_list, recorder=None):
        self.config = config
        self.ip_addr_list = ip_addr_list
        self._config_checker()
        self.msg_queue = multiprocessing.Queue()
        self.context = self._get_worker_context()
        self.workers = []
        self.state = 1
        self.ipaddr_to_status = {}
        self.job_total_count = 1
        self.job_count = 0
        if recorder:
            self.recorder = recorder
        for idx in range(len(ip_addr_list)):
            self.view.status_list.append("%s(%s)" % (
                ip_addr_list[idx]['name'], ip_addr_list[idx]['ip']))

            self.ipaddr_to_status[ip_addr_list[idx]['ip']] = {
                'name': ip_addr_list[idx]['name'],
                'status': utils.MSG_STATUS.disconnected,
                'index': idx,
                'total_count': 0,
                'loss_count':  0
            }
        if self.config['WORK_COUNT']:
            self.job_total_count = self.config['WORK_COUNT'] * \
                len(ip_addr_list)

    def view_callback(self, msg):
        self.job_count += 1
        self.ipaddr_to_status[msg.ip]['status'] = msg.status
        self.ipaddr_to_status[msg.ip]['total_count'] += 1

        if msg.status == utils.MSG_STATUS.disconnected:
            self.ipaddr_to_status[msg.ip]['loss_count'] += 1
        loss_rate = 100 * \
            self.ipaddr_to_status[msg.ip]['loss_count'] / \
            self.ipaddr_to_status[msg.ip]['total_count']
        log = "%s(%s) 丢包率:%d%%" % (
            self.ipaddr_to_status[msg.ip]['name'], msg.ip, loss_rate)
        self.view.status_list.update(
            self.ipaddr_to_status[msg.ip]['index'], log)
        # self.recorder.write(
        #     msg, msg_type=datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
        if loss_rate > 10:
            self.view.status_list.set_red(
                self.ipaddr_to_status[msg.ip]['index'])
        else:
            self.view.status_list.set_green(
                self.ipaddr_to_status[msg.ip]['index'])
        self.view.status_msg.set("%d%%( 总共%d次测试，已完成%d次)"
                                 % (self.job_count*100/self.job_total_count, self.job_total_count, self.job_count,))


if __name__ == "__main__":
    c = Controller()
    c.initialize_worker(utils.load_config('./config.txt'),
                        utils.load_ipaddr('./ipaddrs.txt'))
    c.do_work()
    # print(c.ip_addr_list)
    # print(c._split_list(c.ip_addr_list, 3))
