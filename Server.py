import os
from subprocess import check_output
from threading import Thread

import socket

from Sender import Sender
from Receiver import Receiver


class Session(Thread):
    def __init__(self, func):
        Thread.__init__(self)
        self.func = func

    def run(self):
        self.func()


class Server:
    def __init__(self, port=8480, dir_f="."):
        self.dir = dir_f
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', port))
        self.port = port

    def start(self):
        os.chdir(self.dir)
        while True:
            msg, client_address = self.sock.recvfrom(4096)
            addr_c, _ = client_address
            data = msg.decode('utf-8').split(" ")
            output = ""

            if data[0] == 'ls':
                output = check_output(['ls'])
            elif data[0] == 'get' and len(data) == 3:
                filename = data[1]
                port = int(data[2])
                Session(lambda: Sender(addr_c, port, filename).start()).start()
            elif data[0] == 'put' and len(data) == 3:
                port = int(data[2])
                Session(lambda: Receiver(port).start()).start()
            else:
                continue

            if output != "":
                self.sock.sendto(output, client_address)
