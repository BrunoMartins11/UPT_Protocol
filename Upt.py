import socket
from random import randint

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
    sock.listen(10)
    while True:
        conn, addr = sock.accept()
        while True:
            data = conn.recv(4096)
            if data == 'exit':
                break
            conn.send(b'Received')
        conn.close()

def client(port):
    sock = socket.socket()
    sock.connect(('127.0.0.1', port))
    while True:
        cmd = input("> ")
        sock.send(str.encode(cmd))
        print(sock.recv(4096))
        if cmd == 'exit':
            break

if __name__ == '__main__':
    welcome_str = '''Choose mode:
    1 - Server
    2 - Client
    0 - Exit'''
    print(welcome_str)
    while True:
        i = input("> ")
        if i == '1':
            directory = input("File directory? [default='.']")
            if directory == '':
                directory = '.'
            server(directory)
            i = '0'
        elif i == '2':
            port = int(input("Port number? "))
            client(port)
            i = '0'

        if i == '0':
            break
