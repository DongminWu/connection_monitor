import platform
from enum import Enum
import os

MSG_STATUS = Enum('MSG_STATUS', 'invalid disconnected reconnected')


def is_windows():
    return platform.system() == "Windows"



def parse_txt(file):
    ret = []
    if not os.path.exists(file):
        raise ValueError(file+"doesn't exist.")
    with open(file, 'rb') as f:
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

def load_config(path):
    ret ={}
    res = parse_txt(path)
    for each in res:
        ret[each[0]] = int(each[1])
    return ret
        
def load_ipaddr(path):
    ret = []
    res = parse_txt(path)
    for each in res:
        ret.append({'ip':each[0], 'name':each[1], 'status': MSG_STATUS.disconnected})
    return ret



class MessagePacket:
    def __init__(self, ip, name, status):
        self.ip = ip
        self.name = name
        self.status = status

    def __str__(self):
        if self.status == MSG_STATUS.invalid:
            return 'this msg packet is invalid'
        elif self.status == MSG_STATUS.disconnected:
            return "%s/%s 断开" % (self.ip, self.name)
        elif self.status == MSG_STATUS.reconnected:
            return "%s/%s 链接" % (self.ip, self.name)
    