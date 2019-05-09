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
        print("[Sender window]: Acking packet")
        if self.state == CC.SLOW_START:
            print("[Sender window]: Acking in slow start")
            self.slow_start(seqno)
        elif self.state == CC.AVOID_CONGEST:
            print("[Sender window]: Acking in avoid congest")
            self.avoid(seqno)
        else:
            print("[Sender window]: Acking going to quirck r")
            self.quick_r(seqno)

        print("[Sender window]: Acking packet, " + str(len(self.msg_window)) + " packets in the window")
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
                print("[Sender window]: Acking packet and deleted sent, " + str(len(self.msg_window)) + " packets in the window")
                return True
        return False

    def slow_start(self, seqno):
        print("[Sender window]: In slow start func")
        if self.cwnd >= self.ssthresh:
            print("[Sender window]: In slow start func, cwnd > ssthresh")
            self.state = CC.AVOID_CONGEST
            print("[Sender window]: In slow start func, set state to avoid congest and go avoid")
            self.avoid(seqno)
        elif list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window)):
            print("[Sender window]: In slow start func, window has packet sent with our seqno")
            self.cwnd += 1
            self.dup_ack = 0
            self.action = CC.TRANS
        else:
            print("[Sender window]: In slow start func, got a dup ack")
            self.dup_ack += 1
            if self.dup_ack == 3:
                print("[Sender window]: In slow start func, got a dup ack 3 times, going to recover")
                self.to_quick_r()

    def avoid(self, seqno):
        print("[Sender window]: In avoid congest function")
        if list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window)):
            print("[Sender window]: In avoid congest func, window has packet sent with our seqno")
            self.cwnd += (1 / self.cwnd)
            self.dup_ack = 0
            self.action = CC.TRANS
        else:
            print("[Sender window]: In avoid congest func, got dup ack")
            self.dup_ack += 1
            if self.dup_ack == 3:
                print("[Sender window]: In avoid congest func, got dup ack 2 times, going to quick recover")
                self.to_quick_r()

    def quick_r(self, seqno):
        print("[Sender window]: In quick recov func")
        old_ack = list(filter(lambda x: x[2] and x[0] == seqno, self.msg_window))
        if not old_ack:
            print("[Sender window]: In quick recov func, new ack going to transmission state")
            self.cwnd += 1
            self.action = CC.TRANS
        elif old_ack:
            print("[Sender window]: In quick recov func, old ack going to avoid congest state")
            self.state = CC.AVOID_CONGEST
            self.cwnd = self.ssthresh
            self.dup_ack = 0

    def to_quick_r(self):
        print("[Sender window]: In to_quick_r, adjusting stuff")
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
        print("[Sender window]: to_send " + str(len(packets)) + " packets")
        return packets

    def to_ack(self):
        packets = []
        i = 0
        while i < len(self.msg_window):
            if self.msg_window[i][2]:
                packets.append((self.msg_window[i], i))
            i += 1
        print("[Sender window]: to_ack " + str(len(packets)) + " packets")
        return packets