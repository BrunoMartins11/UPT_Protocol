import os
import random
from subprocess import check_output
from threading import Thread
import socket
import json

from Sender import Sender
from Receiver import Receiver

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.fernet import Fernet
import cryptography.hazmat.primitives.serialization

class Session(Thread):
    def __init__(self, client_address, port, key):
        Thread.__init__(self)
        self.client_address = client_address
        self.key = key
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
            self.client_address = client_address
            self.sock.settimeout(None)
            addr_c, _ = client_address
            msg = self.key.decrypt(msg)
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

            self.sock.sendto(self.key.encrypt(output), client_address)


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
            pub_key = None

            if data[0] == 'login' and len(data) == 3:
                if data[1] in self.users and self.users[data[1]]['password'] == data[2]:
                    pub_key = self.users[data[1]]['public_key']
                else:
                    self.sock.sendto(b'Invalid username or password', client_address)
                    continue
            elif data[0] == 'register' and len(data) > 2:
                if data[1] not in self.users:
                    pub_key = ' '.join(data[3:])
                    self.users[data[1]] = {
                        'name': data[1],
                        'password': data[2],
                        'public_key': pub_key
                    }
                    self.store_users()
                else:
                    self.sock.sendto(b'Username taken', client_address)
                    continue

            if pub_key is None:
                self.sock.sendto(b'Invalid command', client_address)
                continue

            public_key = cryptography.hazmat.primitives.serialization.load_pem_public_key(
                str.encode(pub_key),
                backend=default_backend()
            )

            # Generate symetric key
            simetric_key = Fernet.generate_key()
            port = random.randint(10000, 40000)
            msg = 'Valid {} {}'.format(port, simetric_key.decode())
            output = public_key.encrypt(str.encode(msg), PKCS1v15())
            Session(client_address, port, Fernet(simetric_key)).start()

            self.sock.sendto(output, client_address)

