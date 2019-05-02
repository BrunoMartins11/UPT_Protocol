from Upt_server import server
from Upt_client import client

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
            address = 'localhost'
            client(address, port)
            i = '0'

        if i == '0':
            break
