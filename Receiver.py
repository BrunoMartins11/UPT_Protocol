import socket

import time
import argparse

import Packet
import Connection


class Receiver:
    def __init__(self, listenport=33122, timeout_t=10):
        self.timeout = timeout_t
        self.last_cleanup = time.time()
        self.port = listenport
        self.host = ''

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(timeout_t)
        self.s.bind((self.host, self.port))

        self.connections = {}
        self.MESSAGE_HANDLER = {
            'start': self.handle_start,
            'data': self.handle_data,
            'end': self.handle_end,
            'ack': self._handle_ack
        }

    def start(self):
        while True:
            try:
                message, address = self.receive()
                msg_type, seqno, data, checksum = Packet.split_packet(message)

                if Packet.validate_checksum(message):
                    self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data, address)

                if time.time() - self.last_cleanup > self.timeout:
                    self.cleanup()

                if len(self.connections) == 0:
                    break

            except socket.timeout:
                self.cleanup()
                raise TimeoutError
            except KeyboardInterrupt:
                break
            except ValueError:
                pass

    def receive(self):
        return self.s.recvfrom(4096)

    def send(self, message, address):
        self.s.sendto(message, address)

    def send_ack(self, seqno, address):
        m = b"".join([b'ack|', bytes(str(seqno).encode()), b'|'])
        checksum = Packet.generate_checksum(m)
        message = m + checksum
        self.send(message, address)

    def handle_start(self, seqno, data, address):
        if address not in self.connections:
            self.connections[address] = Connection.Connection(address[0], address[1], seqno, data.decode())
        conn = self.connections[address]
        ackno, res_data = conn.ack(seqno, data)
        self.send_ack(ackno, address)

    def handle_data(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data)
            for l in res_data:
                conn.record(l)
            self.send_ack(ackno, address)

    def handle_end(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data)
            for l in res_data:
                conn.record(l)
            self.send_ack(ackno, address)
            conn.end()
            del self.connections[address]

    def _handle_ack(self, seqno, data, address):
        pass

    def _handle_other(self, seqno, data, address):
        pass

    def cleanup(self):
        for address in list(self.connections):
            conn = self.connections[address]
            if time.time() - conn.updated > self.timeout:
                conn.end()
                del self.connections[address]
        self.last_cleanup = time.time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receive files via a fast and secure UDP channel.",
                                     epilog="Unicorns powered this")
    parser.add_argument("-p", "--port", help="UDP port, defaults to 33122", type=int, default=33122)
    parser.add_argument("-t", "--timeout", help="Timeout for each socket, defaults to 3s", type=int, default=10)
    args = parser.parse_args()

    r = Receiver(args.port, args.timeout)
    r.start()
