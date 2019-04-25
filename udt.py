import random
import socket

# DROP_PROB = 1

# unreliable channel
def send(packet, sock, addr):
    sock.sendto(packet, addr)
    return

def recv(sock):
    packet, addr = sock.recvfrom(1024) # change this?
    return packet, addr
