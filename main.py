from worker import Worker
from recorder import Recorder

import config

import os

class Controller:
    def __init__(self):
        self.ip_addr_list = []
        self._parse_ip_addr()

    def _parse_ip_addr(self):
        if not config.IP_ADDR_FILE:
            raise ValueError("config.py needs a value for IP_ADDR_FILE")
        if not os.path.exists(config.IP_ADDR_FILE):
            raise ValueError(config.IP_ADDR_FILE+"doesn't exist.")

        with open(config.IP_ADDR_FILE) as f:
            lines = f.readlines()
            for l in lines:
                info = l.strip().split(',')
                self.ip_addr_list.append({'ip':info[0], 'name':info[1]})
        
    

    '''
        TODO:
            1. 做个线程池的东西
            2. 把测试的跑起来
                链接controller， worker， recorder
            3. 做个gui

    '''


    
    
    

if __name__ == "__main__":
    c = Controller()
    print(c.ip_addr_list)