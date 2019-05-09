import socket
import json
from random import randint
from time import sleep

from Sender import Sender
from Receiver import Receiver

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import NoEncryption, Encoding, PrivateFormat, PublicFormat
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.fernet import Fernet


class Client:
    def __init__(self, s_addr, s_port, m_port):
        self.server_addr = s_addr
        self.server_port = s_port
        self.port = m_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.port))
        self.load_keys()

    def load_keys(self):
        try:
            self.keys = json.load(open(".keys", "r"))
        except IOError:
            self.keys = {}

    def store_keys(self):
        json.dump(self.keys, open(".keys", "w"))


    def generate_user(self, user, password):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        private_bytes = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        public_bytes = private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.PKCS1)
        self.keys[user] = {
            'password': password,
            'private_key': private_bytes.decode(),
            'public_key': public_bytes.decode(),
        }
        self.store_keys()
        return private_key, public_bytes


    def start(self):
        while True:
            cmd = input("> ").rstrip().split(" ")
            action = None
            request = ""
            private_key = None

            if cmd[0] == 'login' and len(cmd) == 3:
                request = ' '.join(cmd)
            elif cmd[0] == 'register' and len(cmd) == 3:
                if cmd[1] not in self.keys:
                    private_key, public_bytes = self.generate_user(cmd[1], cmd[2])
                    cmd.append(public_bytes.decode())
                    request = ' '.join(cmd)
                else:
                    print('Username taken')
                    continue
            else:
                print('Invalid command')
                continue

            self.sock.sendto(str.encode(request, 'utf-8'), (self.server_addr, self.server_port))
            response = self.sock.recv(4096)
            output = private_key.decrypt(response, PKCS1v15()).decode().split(' ')
            if output[0] == 'Valid' and len(output) == 3:
                self.server_port = int(output[1])
                self.session(Fernet(str.encode(output[2])))
                return
            else:
                print('Error', ' '.join(output))

    def session(self, key):
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

            self.send(request, key)
            if action is not None:
                try:
                    action()
                except TimeoutError:
                    print("Request timed out")
                except IOError:
                    print("IO Error")

            response = self.output(key)
            print(response)
            if 'Connection timed out' == response:
                return

    def send(self, msg, key):
        msg = key.encrypt(str.encode(msg, 'utf-8'))
        self.sock.sendto(msg, (self.server_addr, self.server_port))

    def output(self, key):
        response = self.sock.recv(4096)
        return key.decrypt(response).decode()

