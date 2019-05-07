import os
import random
from subprocess import check_output
from threading import Thread
import socket
import json

from Sender import Sender
from Receiver import Receiver

class Session(Thread):
    def __init__(self, client_address, port):
        Thread.__init__(self)
        self.client_address = client_address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', port))

    def run(self):
        while True:
            self.sock.settimeout(10 * 60) # Timeout after 10 minutes
            try:
                msg, client_address = self.sock.recvfrom(4096)
            except socket.timeout:
                self.sock.sendto(b'Connection timed out', self.client_address)
                print("Client at {} timed out".format(self.client_address))
                exit()
            if client_address != self.client_address:
                continue
            self.sock.settimeout(None)
            addr_c, _ = client_address
            data = msg.decode('utf-8').split(" ")
            output = b'Invalid command'

            if data[0] == 'ls':
                output = check_output(['ls'])
            elif data[0] == 'get' and len(data) == 3:
                filename = data[1]
                port = int(data[2])
                Sender(addr_c, port, filename).start()
                output = b'Sent'
            elif data[0] == 'put' and len(data) == 3:
                port = int(data[2])
                Receiver(port).start()
                output = b'Received'

            self.sock.sendto(output, client_address)


class Server:
    def __init__(self, port=8480, dir_f="."):
        self.dir = dir_f
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', port))
        self.port = port
        self.load_users()

    def load_users(self):
        try:
            self.users = json.load(open(".users", "r"))
        except IOError:
            self.users = {}

    def store_users(self):
        json.dump(self.users, open(".users", "w"))

    def start(self):
        os.chdir(self.dir)
        while True:
            msg, client_address = self.sock.recvfrom(4096)
            addr_c, _ = client_address
            data = msg.decode('utf-8').split(" ")
            output = b'Invalid command'
            user_logged_in = False

            if data[0] == 'login' and len(data) == 3:
                if data[1] in self.users and self.users[data[1]]['password'] == data[2]:
                    user_logged_in = True
                else:
                    output = b'Invalid username or password'

            elif data[0] == 'register' and len(data) == 3:
                if data[1] not in self.users:
                    self.users[data[1]] = { 'name': data[1], 'password': data[2] }
                    self.store_users()
                    user_logged_in = True
                else:
                    output = b'Username taken'

            if user_logged_in:
                port = random.randint(10000, 40000)
                Session(client_address, port).start()
                output = str.encode('Valid {}'.format(port))

            self.sock.sendto(output, client_address)

