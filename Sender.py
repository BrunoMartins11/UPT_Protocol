import argparse
import os
import random
import socket
from random import randint

import Packet


class Sender:

    def __init__(self, dest, port, filename, timeout=10):
        self.current_state = 0
        self.dest = dest
        self.dport = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.infile = open(filename, "rb")
        self.filesize = 0
        self.msg_window = []
        self.initial_sn = randint(0, 65535)
        self.current_sn = self.initial_sn
        self.rtimeout = timeout
        self.filename = filename
        self.MESSAGE_HANDLER = {
            'ack': self.handle_ack
        }

    def receive(self, timeout=None):
        self.sock.settimeout(timeout)
        try:
            return self.sock.recv(4096)
        except (socket.timeout, socket.error):
            return None

    def send(self, message, address=None):
        if address is None:
            address = (self.dest, self.dport)
        self.sock.sendto(message, address)

    def start(self):
        self.load_file()

        # 0: Transfer not started
        # 1: Transfer in progress
        # 2: Transfer ending
        # 3: Transfer ended

        while True:
            try:
                if self.current_state == 0:
                    self.send(Packet.make_packet('start', self.msg_window[0][0], self.msg_window[0][1]),
                              (self.dest, self.dport))
                    self.msg_window[0][2] = True
                elif self.current_state == 1:
                    self.send_next_data()
                elif self.current_state == 2:
                    self.send(Packet.make_packet('end', self.msg_window[0][0], self.msg_window[0][1]),
                              (self.dest, self.dport))
                    self.msg_window[0][2] = True
                elif self.current_state == 3:
                    exit()

                message = self.receive(self.rtimeout)

                if message:
                    msg_type, seqno, data, checksum = Packet.split_packet(message)
                    if Packet.validate_checksum(message):
                        self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data)
                else:
                    pass
            except (KeyboardInterrupt, SystemExit):
                exit()
            except:
                pass

    def increment_state(self):
        self.current_state += 1

    def load_file(self):
        # (data (bytearray), seqno (int), sent (bool))
        # seqno incremented by the number of bytes in the current packet.

        # first packet
        # reset initial sn
        self.msg_window.append([self.current_sn, self.filename.encode('utf-8'), False])
        self.initial_sn += len(self.filename.encode('utf-8'))
        self.current_sn = self.initial_sn

        with open(self.filename, 'rb') as sending_file:
            self.filesize = os.stat(self.filename).st_size

            while (self.msg_window.__len__() < 5) and (self.filesize > (self.current_sn - self.initial_sn)):
                sending_file.seek(self.current_sn - self.initial_sn)
                next_packet = sending_file.read(1458)
                self.msg_window.append([self.current_sn, next_packet, False])
                self.current_sn += len(next_packet)

            if self.msg_window.__len__() < 5:
                packet_size = len(self.msg_window[self.msg_window.__len__() - 1][1])
                while self.msg_window.__len__() < 5:
                    print("l")
                    self.current_sn += packet_size
                    self.msg_window.append([self.current_sn, b'', False])  # 'end' packet

    def update_sliding_window(self):
        with open(self.filename, 'rb') as sending_file:
            # check to see if the window is full
            if self.msg_window.__len__() < 5:
                # if the window is not full, and there is still more data in the file to retrieve
                while ((self.msg_window.__len__() < 5) and
                       (self.filesize > (self.current_sn - self.initial_sn))):
                    sending_file.seek(self.current_sn - self.initial_sn)
                    next_packet = sending_file.read(1458)
                    self.msg_window.append([self.current_sn, next_packet, False])
                    self.current_sn += len(next_packet)
            else:
                pass

        if self.current_state == 0:
            self.increment_state()
        if self.msg_window.__len__() <= 1:
            self.increment_state()
        pass

    def resend_data(self):
        try:
            i = 0
            while i < len(self.msg_window):
                if self.msg_window[i]:
                    self.send(Packet.make_packet('data', self.msg_window[i][0], self.msg_window[i][1]),
                              (self.dest, self.dport))
                    self.msg_window[i][2] = True
                i += 1
        except:
            pass

    def send_next_data(self):
        if len(self.msg_window) > 0:
            packet_to_send = False
            i = 0
            while (not packet_to_send) and (i < len(self.msg_window)):
                if not self.msg_window[i][2]:
                    packet_to_send = True
                else:
                    i += 1

            if packet_to_send:
                while i < len(self.msg_window):
                    self.send(Packet.make_packet('data', self.msg_window[i][0], self.msg_window[i][1]),
                              (self.dest, self.dport))
                    self.msg_window[i][2] = True
                    i += 1
        pass

    def handle_ack(self, seqno, data):
        temp_packet = []
        temp_index = 0

        for index in list(range(self.msg_window.__len__())):
            if seqno == self.msg_window[index][0]:
                temp_packet = self.msg_window[index]
                temp_index = index
                break

        if len(temp_packet) > 0:
            # if the packet has been sent previously accept it
            if self.msg_window[temp_index][2]:
                del self.msg_window[temp_index]
                self.update_sliding_window()
        pass

    def _handle_other(self, seqno, data):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send files via a fast and secure UDP channel.",
                                     epilog="Unicorns powered this")
    parser.add_argument("-f", "--file", help="File to send", required=True)
    parser.add_argument("-p", "--port", help="UDP port, defaults to 33122", type=int, default=33122)
    parser.add_argument("-a", "--address", help="Receiver's address, defaults to localhost", default="localhost")
    args = parser.parse_args()

    s = Sender(args.address, args.port, args.file)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
