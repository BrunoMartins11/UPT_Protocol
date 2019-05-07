import os
import utils as CC
from random import randint


class Window:

    def __init__(self, ws, filename):
        self.rwindow = 0
        self.msg_window = []
        self.initial_sn = randint(0, 65535)
        self.current_sn = self.initial_sn
        self.infile = open(filename, "rb")
        self.filesize = 0
        self.filename = filename
        self.ws = ws
        self.cwnd = 1
        self.dupack = 0
        self.ssthresh = 64
        self.state = CC.SLOW_START
        self.action = CC.TRANS

    def ack(self, seqno, data):
        self.rwindow = int(data)
        if self.state == CC.SLOW_START:
            self.slow_start(seqno)
        elif self.state == CC.AVOID_CONGEST:
            self.avoid(seqno)
        else:
            self.quick_r(seqno)

        # Go-Back-N
        temp_packet = []
        temp_index = 0

        for index in list(range(len(self.msg_window))):
            if seqno == self.msg_window[index][0]:
                temp_packet = self.msg_window[index]
                temp_index = index
                break

        if len(temp_packet) > 0:
            if self.msg_window[temp_index][2]:
                del self.msg_window[temp_index]
                self.update_sliding_window()

    def slow_start(self, acknum):
        if self.cwnd >= self.ssthresh:
            self.state = CC.AVOID_CONGEST
            self.avoid(acknum)
        elif acknum == self.base:
            self.cwnd += 1
            self.dupack = 0
            self.action = CC.TRANS
        else:
            self.dupack += 1
            if self.dupack == 3:
                self.to_quick_r()

    def avoid(self, acknum):
        if acknum == self.base:
            self.cwnd += (1 / self.cwnd)
            self.dupack = 0
            self.action = CC.TRANS
        else:
            self.dupack += 1
            if self.dupack == 3:
                self.to_quick_r()

    def quick_r(self, acknum):
        if acknum < self.base:
            self.cwnd += 1
            self.action = CC.TRANS
        elif acknum == self.base:
            self.state = CC.AVOID_CONGEST
            self.cwnd = self.ssthresh
            self.dupack = 0

    def to_quick_r(self):
        self.state = CC.QUICK_RECOVER
        self.action = CC.RETRANS
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3

    def update_sliding_window(self):
        with open(self.filename, 'rb') as sending_file:
            if len(self.msg_window) < 5:
                while ((len(self.msg_window) < 5) and
                       (self.filesize > (self.current_sn - self.initial_sn))):
                    sending_file.seek(self.current_sn - self.initial_sn)
                    next_packet = sending_file.read(1458)
                    self.msg_window.append([self.current_sn, next_packet, False])
                    self.current_sn += len(next_packet)

    def can_send(self, rwnd):
        return len(self.msg_window) < min([self.cwnd, self.ws, rwnd])

    def load_file(self):
        # seqno += number of bytes in the current packet

        self.msg_window.append([self.current_sn, self.filename.encode('utf-8'), False])
        self.initial_sn += len(self.filename.encode('utf-8'))
        self.current_sn = self.initial_sn

        with open(self.filename, 'rb') as sending_file:
            self.filesize = os.stat(self.filename).st_size

            while (len(self.msg_window) < 5) and (self.filesize > (self.current_sn - self.initial_sn)):
                sending_file.seek(self.current_sn - self.initial_sn)
                next_packet = sending_file.read(1458)
                self.msg_window.append([self.current_sn, next_packet, False])
                self.current_sn += len(next_packet)

            if len(self.msg_window) < 5:
                self.msg_window.append([self.current_sn, b'', False])  # 'end' packet

    # MERDAS

    def timeout(self):
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupack = 0
        self.state = CC.SLOW_START
        self.action = CC.RETRANS
