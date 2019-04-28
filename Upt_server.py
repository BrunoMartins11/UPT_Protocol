import socket
from random import randint
from subprocess import check_output
import os

def run_ls(args):
    return check_output(args)

cmds = {
        "ls": lambda a: run_ls(["ls"] + a),
        }

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
        while True:
            data = str(conn.recv(4096).decode("utf-8"))
            data = data.split(" ")
            if data[0] == 'exit':
                break
            if data[0] in cmds:
                out = cmds[data[0]](data[1:])
            else:
                out = b'Invalid command'
            conn.send(out)
        conn.close()

