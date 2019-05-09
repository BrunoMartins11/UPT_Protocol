import utils as CC
from random import randint


class Window:

    def __init__(self, ws):
        self.msg_window = []
        self.initial_sn = randint(0, 65535)
        self.current_sn = self.initial_sn
        self.ws = ws
        self.cwnd = 1
        self.dup_ack = 0
        self.ssthresh = 64
        self.state = CC.SLOW_START
        self.action = CC.TRANS

    def push(self, data):
        self.msg_window.append(data)

    def ack(self, seqno):
        if self.state == CC.SLOW_START:
            self.slow_start(seqno)
        elif self.state == CC.AVOID_CONGEST:
            self.avoid(seqno)
        else:
            self.quick_r(seqno)

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
                return True
        return False

    def slow_start(self, seqno):
        if self.cwnd >= self.ssthresh:
            self.state = CC.AVOID_CONGEST
            self.avoid(seqno)
        elif list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window)):
            self.cwnd += 1
            self.dup_ack = 0
            self.action = CC.TRANS
        else:
            self.dup_ack += 1
            if self.dup_ack == 3:
                self.to_quick_r()

    def avoid(self, seqno):
        if list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window)):
            self.cwnd += (1 / self.cwnd)
            self.dup_ack = 0
            self.action = CC.TRANS
        else:
            self.dup_ack += 1
            if self.dup_ack == 3:
                self.to_quick_r()

    def quick_r(self, seqno):
        old_ack = list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window))
        if not old_ack:
            self.cwnd += 1
            self.action = CC.TRANS
        elif old_ack:
            self.state = CC.AVOID_CONGEST
            self.cwnd = self.ssthresh
            self.dup_ack = 0

    def to_quick_r(self):
        self.state = CC.QUICK_RECOVER
        self.action = CC.RETRANS
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3

    def can_send(self, rwnd):
        return len(self.msg_window) < min([self.cwnd, self.ws, rwnd])

    def timeout(self):
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dup_ack = 0
        self.state = CC.SLOW_START
        self.action = CC.RETRANS

    def to_send(self):
        packets = []
        i = 0
        while i < len(self.msg_window):
            if not self.msg_window[i][2]:
                packets.append((self.msg_window[i], i))
            i += 1
        return packets

    def to_ack(self):
        packets = []
        i = 0
        while i < len(self.msg_window):
            if self.msg_window[i][2]:
                packets.append((self.msg_window[i], i))
            i += 1
        return packets