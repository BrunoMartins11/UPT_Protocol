import socket
from random import randint
from Receiver import Receiver
from Sender import Sender

def client(port):
    sock = socket.socket()
    sock.connect(('127.0.0.1', port))
    while True:
        cmd = input("> ")
        cmd = cmd.split(" ")
        if cmd[0] == 'get':
            port = randint(10000,40000)
            address = "localhost"
            timeout = 3
            request = "get {} {} {}".format(address, port, cmd[1])
            sock.send(str.encode(request))
            Receiver(port, timeout).start()
        elif cmd[0] == 'put':
            sock.send(str.encode(cmd[0]))
            response = sock.recv(4096).decode("utf-8")
            response = response.split(" ")
            Sender(response[1], int(response[2]), cmd[1]).start()
        else:
            sock.send(str.encode(" ".join(cmd)))
        if cmd[0] == 'exit':
            break
        print(sock.recv(4096).decode("utf-8"))

