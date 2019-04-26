import time


class Connection:
    def __init__(self, host, port, start_seq, filename):
        self.updated = time.time()
        self.current_seqno = start_seq  # expect to ack from the start_seqno
        self.host = host
        self.port = port
        self.max_buf_size = 5
        self.outfile = open("reV_{0}".format(filename), "wb")
        self.seqnums = {}  # enforce single instance of each seqno

    def ack(self, seqno, data):
        res_data = []
        self.updated = time.time()
        if (seqno == self.current_seqno) and self.seqnums.__len__() <= self.max_buf_size:
            self.seqnums[seqno] = data
            for n in sorted(self.seqnums.keys()):
                if n == self.current_seqno:
                    self.current_seqno += len(data)
                    res_data.append(self.seqnums[n])
                    del self.seqnums[n]
                    break

        # return seqno of the last packet received
        return (self.current_seqno - len(data)), res_data

    def record(self, data):
        self.outfile.write(data)
        self.outfile.flush()

    def end(self):
        self.outfile.close()
