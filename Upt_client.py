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
        request = ''
        action = None
        if cmd[0] == 'get':
            port = randint(10000,40000)
            timeout = 3
            request = "get {} {} {}".format(address, port, cmd[1])
            action = lambda: Receiver(port, timeout).start()
        elif cmd[0] == 'put':
            port = randint(10000,40000)
            request = 'put {}'.format(port)
            action = lambda: Sender(address, port, cmd[1]).start()
        elif cmd[0] == 'exit':
            break
        else:
            request = " ".join(cmd)

        print("REQUESTING: {}".format(request))
        sock.send(str.encode(request))
        if action is not None:
            action()
        print(sock.recv(4096).decode("utf-8"))

