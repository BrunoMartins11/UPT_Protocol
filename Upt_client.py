import socket
from random import randint
from Receiver import Receiver
from Sender import Sender

def client(address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((address, port))
    while True:
        cmd = input("> ")
        cmd = cmd.split(" ")
        if cmd[0] == 'get':
            port = randint(10000,40000)
            timeout = 3
            request = "get {} {} {}".format(address, port, cmd[1])
            print("REQUESTING: {}".format(request))
            sock.send(str.encode(request))
            Receiver(port, timeout).start()
        elif cmd[0] == 'put':
            port = randint(10000,40000)
            request = str.encode('put {}'.format(port))
            print("REQUESTING: {}".format(request))
            sock.send(request)
            Sender(address, port, cmd[1]).start()
        else:
            sock.send(str.encode(" ".join(cmd)))
        if cmd[0] == 'exit':
            break
        print(sock.recv(4096).decode("utf-8"))

