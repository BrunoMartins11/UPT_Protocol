import argparse
import packet
import socket
import sys
import _thread
import time
import udt

from timer import Timer

receiver_addr = ('localhost', 1234)
sender_addr = ('localhost', 0)
PACKET_SIZE = 512
SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5
WINDOW_SIZE = 4

# Shared resources across threads
base = 0
mutex = _thread.allocate_lock()
send_timer = Timer(TIMEOUT_INTERVAL)


def receive_file(sock, filename):
    try:
        file = open(filename, 'wb')
    except IOError:
        print('Unable to open', filename)
        return 1

    expected_num = 0
    while True:
        pkt, addr = udt.recv(sock)
        if not pkt:
            break
        seq_num, data = packet.extract(pkt)
        print('Got packet', seq_num)

        if seq_num == expected_num:
            print('Got expected packet')
            print('Sending ACK', expected_num)
            pkt = packet.make(expected_num)
            udt.send(pkt, sock, addr)
            expected_num += 1
            file.write(data)
        else:
            print('Sending ACK', expected_num - 1)
            pkt = packet.make(expected_num - 1)
            udt.send(pkt, sock, addr)
    file.close()


def set_window_size(num_packets):
    global base
    return min(WINDOW_SIZE, num_packets - base)


def send_file(sock, filename):
    global mutex
    global base
    global send_timer

    try:
        file = open(filename, 'rb')
    except IOError:
        print('Unable to open', filename)
        return 1

    packets = []
    seq_num = 0
    while True:
        data = file.read(PACKET_SIZE)
        if not data:
            break
        packets.append(packet.make(seq_num, data))
        seq_num += 1

    num_packets = len(packets)
    print("Numero package: ", num_packets)
    window_size = set_window_size(num_packets)
    next_to_send = 0
    base = 0

    # Start the receiver thread
    _thread.start_new_thread(receive_ack, (sock,))

    while base < num_packets:
        mutex.acquire()
        # Send all the packets in the window
        while next_to_send < base + window_size:
            print('Sending packet', next_to_send)
            udt.send(packets[next_to_send], sock, receiver_addr)
            next_to_send += 1

        # Start the timer
        if not send_timer.running():
            print('Starting timer')
            send_timer.start()

        # Wait until timer or ACK
        while send_timer.running() and not send_timer.timeout():
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if send_timer.timeout():
            send_timer.stop()
            next_to_send = base
        else:
            window_size = set_window_size(num_packets)
        mutex.release()

    # Send empty packet as sentinel
    udt.send(packet.make_empty(), sock, receiver_addr)
    file.close()


# Receive thread
def receive_ack(sock):
    global mutex
    global base
    global send_timer

    while True:
        pkt, _ = udt.recv(sock)
        ack, _ = packet.extract(pkt)

        # If we get an ACK for the first in-flight packet
        print('Got ACK', ack)
        if (ack >= base):
            mutex.acquire()
            base = ack + 1
            print('Base updated', base)
            send_timer.stop()
            mutex.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sender", help="run as sender",
                                           action="store_true")
    parser.add_argument("-r", "--receiver", help="run as receiver",
                                               action="store_true")
    parser.add_argument("-f", "--file", help="file to send/get")
    args = parser.parse_args()

    if args.sender and args.file:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(sender_addr)
        filename = args.file
        send_file(sock, filename)
        sock.close()
    elif args.receiver and args.file:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(receiver_addr)
        filename = args.file
        receive_file(sock, filename)
        sock.close()
    else:
        print("Wrong arguments! Run with --help")
        exit()
