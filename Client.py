import socket

from random import randint
from time import sleep

from Sender import Sender
from Receiver import Receiver


class Client:
    def __init__(self, s_addr, s_port, m_port):
        self.server_addr = s_addr
        self.server_port = s_port
        self.port = m_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.port))

    def start(self):
        while True:
            cmd = input("> ").split(" ")
            action = None
            request = ""

            if cmd[0] == 'ls':
                request = cmd[0]
            elif cmd[0] == 'get' and len(cmd) == 2:
                port_c = randint(10000, 40000)
                request = "get {} {}".format(cmd[1], str(port_c))
                action, s = lambda: Receiver(port_c).start(), False
            elif cmd[0] == 'put' and len(cmd) == 2:
                port_s = randint(10000, 40000)
                request = "put {} {}".format(cmd[1], str(port_s))
                action, s = lambda: Sender(self.server_addr, port_s, cmd[1]).start(), True
            elif cmd[0] == ':q':
                exit()
            else:
                continue

            self.send(request)
            if action is not None:
                try:
                    if s:
                        sleep(0.5)
                    action()
                except TimeoutError:
                    print("Request timed out")
                except IOError:
                    print("IO Error")
            if request == 'ls':
                self.output()

    def send(self, msg):
        self.sock.sendto(str.encode(msg, 'utf-8'), (self.server_addr, self.server_port))

    def output(self):
        print(self.sock.recv(4096).decode('utf-8'))
