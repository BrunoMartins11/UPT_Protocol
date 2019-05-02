import socket
from random import randint
import subprocess
import os
from threading import Thread
from Sender import Sender
from Receiver import Receiver

def run_ls(args):
    return subprocess.check_output(args)

class ClientThread(Thread):
    def __init__(self, func):
        Thread.__init__(self)
        self.func = func

    def run(self):
        self.func()

def server(directory='.'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
    while True:
        payload, client_address = sock.recvfrom(4096)
        print("MESSAGE RECEIVED: {}".format(payload))
        data = payload.decode('utf-8').split(" ")
        if data[0] == 'ls':
            out = run_ls(data)
        elif data[0] == 'get':
            address = data[1]
            port = int(data[2])
            filename = data[3]
            ClientThread(lambda: Sender(address, port, filename).start()).start()
            out = b'Sent'
        elif data[0] == 'put':
            port = int(data[1])
            ClientThread(lambda: Receiver(port, 3).start()).start()
            out = b'Received'
        else:
            out = b'Invalid command'
        sock.sendto(out, client_address)

