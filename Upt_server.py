import socket
from random import randint
from subprocess import check_output
import os
from threading import Thread
from Sender import Sender
from Receiver import Receiver

def run_ls(args):
    return check_output(args)

class ClientThread(Thread):
    def __init__(self, socket):
        Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
            data = str(self.socket.recv(4096).decode("utf-8"))
            print("MESSAGE RECEIVED: {}".format(data))
            data = data.split(" ")
            if data[0] == 'exit':
                break
            if data[0] == 'ls':
                out = run_ls(data)
            elif data[0] == 'get':
                address = data[1]
                port = data[2]
                filename = data[3]
                # print("Sending to {} on port {} => {}".format(address, port, filename))
                Sender(address, int(port), filename).start()
                out = b'Sent'
            elif data[0] == 'put':
                port = randint(10000, 40000)
                cmd = 'Receiving_on: localhost {}'.format(port)
                self.socket.send(str.encode(cmd))
                # print("Receiving on port {}".format(port))
                Receiver(port, 3).start()
                out = b'Received'
            else:
                out = b'Invalid command'
            self.socket.send(out)
        self.socket.close()


def server(directory='.'):
    sock = socket.socket()
    bound = False
    port = 0
    while not bound:
        try:
            port = randint(10000, 40000)
            sock.bind(('', port))
        except Exception as e:
            print(e)
            continue
        bound = True
    print('Server started on port: {}'.format(port))
    os.chdir(directory)
    sock.listen(10)
    while True:
        conn, addr = sock.accept()
        ClientThread(conn).start()

