import socket
from random import randint

def client(port):
    sock = socket.socket()
    sock.connect(('127.0.0.1', port))
    while True:
        cmd = input("> ")
        sock.send(str.encode(cmd))
        if cmd == 'exit':
            break
        print(sock.recv(4096).decode("utf-8"))

