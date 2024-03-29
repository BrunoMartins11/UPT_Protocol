import os

import socket

from math import ceil
import random
import argparse

import Packet
from Window import Window

import utils as consts

def encrypted_sender(dest, port, filename, key):
    print('[Sender]: Encrypting "{}"'.format(filename))
    f = open(filename, "rb").read()
    f = key.encrypt(f)
    new_name = 'enc_{}'.format(filename)
    open(new_name, "wb").write(f)
    Sender(dest, port, new_name).start()
    os.remove('enc_{}'.format(filename))

class Sender:
    def __init__(self, dest, port, filename, timeout_t=10):
        self.current_state = 0
        self.rtimeout = timeout_t
        self.attempts = consts.RESEND_MAX
        self.rwindow = 0

        self.window = Window(10)  # [[seqno, data, sent]]

        self.dest = dest
        self.dport = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))

        self.infile = open(filename, "rb")
        self.filesize = 0
        self.filename = filename
        self.total_packets = ceil(os.stat(filename).st_size / consts.DATA_SIZE)

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
        if random.randint(0, 4) > 0:
            self.sock.sendto(message, address)

    def load_file(self):
        # seqno += number of bytes in the current packet

        self.window.push([self.window.initial_sn, self.filename.encode('utf-8'), False])
        self.window.initial_sn += len(self.filename.encode('utf-8'))
        self.window.current_sn = self.window.initial_sn

        with open(self.filename, 'rb') as sending_file:
            self.filesize = os.stat(self.filename).st_size

            while (self.window.can_send(self.rwindow)) and (
                    self.filesize > (self.window.current_sn - self.window.initial_sn)):
                sending_file.seek(self.window.current_sn - self.window.initial_sn)
                next_packet = sending_file.read(consts.DATA_SIZE)
                self.window.push([self.window.current_sn, next_packet, False])
                self.window.current_sn += len(next_packet)

    def update_sliding_window(self):
        with open(self.filename, 'rb') as sending_file:
            while (self.window.can_send(self.rwindow) and
                   (self.filesize > (self.window.current_sn - self.window.initial_sn))):

                sending_file.seek(self.window.current_sn - self.window.initial_sn)
                next_packet = sending_file.read(consts.DATA_SIZE)
                self.window.push([self.window.current_sn, next_packet, False])
                self.window.current_sn += len(next_packet)

        if self.current_state == 0:
            self.increment_state()
        if self.current_state == 1:
            self.total_packets -= 1
            if self.total_packets == 0:
                self.window.push([self.window.current_sn, b'', False])  # 'end' packet
                self.increment_state()
        elif self.current_state == 2:
            self.increment_state()

    def start(self):
        self.load_file()

        # 0: Transfer not started
        # 1: Transfer in progress
        # 2: Transfer ending
        # 3: Transfer ended

        while True:
            try:
                if self.current_state == 0:
                    self.send(Packet.make_packet('start', self.window.msg_window[0][0], self.window.msg_window[0][1]),
                              (self.dest, self.dport))
                    self.window.msg_window[0][2] = True
                elif self.current_state == 1:
                    self.send_data()
                elif self.current_state == 2:
                    self.send(Packet.make_packet('end', self.window.msg_window[0][0], self.window.msg_window[0][1]),
                              (self.dest, self.dport))
                    self.window.msg_window[0][2] = True
                elif self.current_state >= 3:
                    print("done")
                    self.sock.close()
                    break

                message = self.receive(self.rtimeout)

                if message:
                    msg_type, seqno, data, checksum = Packet.split_packet(message)
                    if Packet.validate_checksum(message):
                        self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data)
                else:
                    self.window.timeout()
                    self.attempts -= 1

                if self.attempts <= 0:
                    raise TimeoutError
            except KeyboardInterrupt:
                break

    def increment_state(self):
        self.current_state += 1

    def send_data(self):
        seqs = []
        if self.window.action == consts.TRANS:
            seqs = self.window.to_send()
        elif self.window.action == consts.RETRANS:
            seqs = self.window.to_ack()

        for index in seqs:
            msg, i = index
            self.send(Packet.make_packet('data', self.window.msg_window[i][0], self.window.msg_window[i][1]),
                      (self.dest, self.dport))
            self.window.msg_window[i][2] = True

    def handle_ack(self, seqno, data):
        self.rwindow = int(data)
        update = self.window.ack(seqno)
        if update:
            self.update_sliding_window()

    def _handle_other(self, seqno, data):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send files via a fast and secure UDP channel.",
                                     epilog="Unicorns powered this")
    parser.add_argument("-f", "--file", help="File to send", required=True)
    parser.add_argument("-p", "--port", help="UDP port, defaults to 33122", type=int, default=33122)
    parser.add_argument("-a", "--address", help="Receiver's address, defaults to localhost", default="localhost")
    parser.add_argument("-n", "--number", help="Number of attempts before closing the connection, defaults to 5",
                        type=int, default=5)

    args = parser.parse_args()

    s = Sender(args.address, args.port, args.file)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
