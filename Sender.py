import os

import socket

import random
import argparse

import Packet
from Window import Window


class Sender:
    def __init__(self, dest, port, filename, timeout_t=10, attempts_n=5):
        self.current_state = 0
        self.dest = dest
        self.dport = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.window = Window(10, filename)  # [[seqno, data, sent]]
        self.rtimeout = timeout_t
        self.attempts = attempts_n
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
        self.window.load_file()

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
                    self.send_next_data()
                elif self.current_state == 2:
                    self.send(Packet.make_packet('end', self.window.msg_window[0][0], self.window.msg_window[0][1]),
                              (self.dest, self.dport))
                    self.window.msg_window[0][2] = True
                elif self.current_state >= 3:
                    break

                message = self.receive(self.rtimeout)

                if message:
                    msg_type, seqno, data, checksum = Packet.split_packet(message)
                    if Packet.validate_checksum(message):
                        self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data)
                else:
                    if self.current_state != 0:
                        self.resend_data()
                        self.attempts -= 1

                if self.attempts <= 0:
                    raise TimeoutError
            except KeyboardInterrupt:
                break

    def increment_state(self):
        self.current_state += 1

    def resend_data(self):
        try:
            i = 0
            while i < len(self.msg_window):
                if self.msg_window[i][2]:
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
        self.window.ack(seqno, data)

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
