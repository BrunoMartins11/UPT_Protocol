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
            cmd = input("> ").rstrip().split(" ")
            action = None
            request = ""

            if cmd[0] == 'login' and len(cmd) == 3:
                request = ' '.join(cmd)
            elif cmd[0] == 'register' and len(cmd) == 3:
                request = ' '.join(cmd)
            else:
                print('Invalid command')
                continue

            self.send(request)
            output = self.sock.recv(4096).decode('utf-8').split(' ')
            if output[0] == 'Valid' and len(output) == 2:
                self.server_port = int(output[1])
                self.session()
                return
            else:
                print(' '.join(output))

    def session(self):
        while True:
            cmd = input("> ").split(" ")
            action = None
            request = ""

            if cmd[0] == 'ls':
                request = cmd[0]
            elif cmd[0] == 'get' and len(cmd) == 2:
                port_c = randint(10000, 40000)
                request = "get {} {}".format(cmd[1], str(port_c))
                action = lambda: Receiver(port_c).start()
            elif cmd[0] == 'put' and len(cmd) == 2:
                port_s = randint(10000, 40000)
                request = "put {} {}".format(cmd[1], str(port_s))
                action = lambda: Sender(self.server_addr, port_s, cmd[1]).start()
            elif cmd[0] == ':q':
                exit()
            else:
                continue

            self.send(request)
            if action is not None:
                try:
                    action()
                except TimeoutError:
                    print("Request timed out")
                except IOError:
                    print("IO Error")

            response = self.output()
            print(response)
            if 'Connection timed out' == response:
                return

    def send(self, msg):
        self.sock.sendto(str.encode(msg, 'utf-8'), (self.server_addr, self.server_port))

    def output(self):
        return self.sock.recv(4096).decode('utf-8')

