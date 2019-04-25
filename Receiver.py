import getopt
import socket
import sys
import time

import Checksum
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
        self.connections = {}  # schema is {(address, port) : Connection}
        self.MESSAGE_HANDLER = {
            'start': self._handle_start,
            'data': self._handle_data,
            'end': self._handle_end,
            'ack': self._handle_ack
        }

    def start(self):
        while True:
            try:
                message, address = self.receive()
                msg_type, seqno, data, checksum = self._split_message(message)
                if debug:
                    print('Received message: {0} {1} {2} {3} {4}'.format(msg_type, seqno, data, sys.getsizeof(data),
                                                                         checksum))
                if Checksum.validate_checksum(message):
                    # If the checksum checks out, handle the message using one of the following methods defined by the
                    # MESSAGE_HANDLER dictionary.
                    self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data, address)

                # If the timeout happens, do a cleanup.
                if time.time() - self.last_cleanup > self.timeout:
                    self._cleanup()
            except socket.timeout:
                self._cleanup()
            except (KeyboardInterrupt, SystemExit):
                exit()
            except ValueError:
                pass

    # waits until packet is received to return
    def receive(self):
        return self.s.recvfrom(4096)

    # sends a message to the specified address. Addresses are in the format:
    #   (IP address, port number)
    def send(self, message, address):
        self.s.sendto(message, address)

    # this sends an ack message to address with specified seqno
    def _send_ack(self, seqno, address):
        m = b"".join([b'ack|', bytes(str(seqno).encode()), b'|'])
        checksum = Checksum.generate_checksum(m)
        # message = "%s%s" % (m, checksum)
        message = m + checksum
        self.send(message, address)

    def _handle_start(self, seqno, data, address):
        if not address in self.connections:
            self.connections[address] = Connection.Connection(address[0], address[1], seqno, data.decode())
        conn = self.connections[address]
        ackno, res_data = conn.ack(seqno, data)
        self._send_ack(ackno, address)

    # ignore packets from uninitiated connections
    def _handle_data(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data)
            for l in res_data:
                conn.record(l)
            self._send_ack(ackno, address)

    # handle end packets
    def _handle_end(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data)
            for l in res_data:
                conn.record(l)
            self._send_ack(ackno, address)

    # I'll do the ack-ing here, buddy
    def _handle_ack(self, seqno, data, address):
        pass

    # handler for packets with unrecognized type
    def _handle_other(self, seqno, data, address):
        pass

    def _split_message(self, message):
        pieces = message.split(b'|')
        msg_type, seqno = pieces[0:2]  # first two elements always treated as msg type and seqno
        checksum = pieces[-1]  # last is always treated as checksum
        data = b'|'.join(pieces[2:-1])  # everything in between is considered data
        return msg_type.decode(), int(seqno), data, checksum

    def _cleanup(self):
        now = time.time()
        for address in list(self.connections):
            conn = self.connections[address]
            if now - conn.updated > self.timeout:
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
    r = Receiver(port,  timeout)
    r.start()
