import platform
from enum import Enum

MSG_STATUS = Enum('MSG_STATUS', 'invalid disconnected reconnected')


def is_windows():
    return platform.system() == "Windows"



class MessagePacket:
    def __init__(self, ip, name, status):
        self.ip = ip
        self.name = name
        self.status = status

    def __str__(self):
        if self.status == MSG_STATUS.invalid:
            return 'this msg packet is invalid'
        elif self.status == MSG_STATUS.disconnected:
            return "%s/%s disconnected" % (self.ip, self.name)
        elif self.status == MSG_STATUS.reconnected:
            return "%s/%s connected" % (self.ip, self.name)
    