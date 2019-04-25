import random
import socket

DROP_PROB = 8

def send(packet, sock, addr):
    sock.sendto(packet, addr)
    return

# unreliable channel
def sendU(packet, sock, addr):
    if random.randint(0, DROP_PROB) > 0:
        sock.sendto(packet, addr)
    return

def recv(sock):
    packet, addr = sock.recvfrom(1024) # change this?
    return packet, addr
