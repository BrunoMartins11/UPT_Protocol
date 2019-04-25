import getopt
import socket
import sys
import time

import Packet
import Connection


class Receiver:
    def __init__(self, listenport=33122, timeout_t=3):
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

                # timeout
                if time.time() - self.last_cleanup >= self.timeout:
                    self.cleanup()

                if self.connections.__len__() == 0:
                    exit()

            except socket.timeout:
                self.cleanup()
            except (KeyboardInterrupt, SystemExit):
                exit()
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
        now = time.time()
        for address in list(self.connections):
            conn = self.connections[address]
            if now - conn.updated >= self.timeout:
                conn.end()
                del self.connections[address]
        self.last_cleanup = now


if __name__ == "__main__":
    def usage():
        print("BEARS-TP Receiver")
        print("-p PORT | --port=PORT The listen port, defaults to 33122")
        print("-t TIMEOUT | --timeout=TIMEOUT Receiver timeout in seconds")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")


    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "p:dt:", ["port=", "debug=", "timeout="])
    except:
        usage()
        exit()

    port = 33122
    debug = False
    timeout = 10

    for o, a in opts:
        if o in ("-p", "--port="):
            port = int(a)
        elif o in ("-t", "--timeout="):
            timeout = int(a)
        elif o in ("-d", "--debug="):
            debug = True
        else:
            print(usage())
            exit()
    r = Receiver(port, timeout)
    r.start()
