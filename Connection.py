import time


class Connection:
    def __init__(self, host, port, start_seq, filename):
        self.wc = 5
        self.updated = time.time()
        self.current_seqno = start_seq
        self.host = host
        self.port = port
        self.max_buf_size = 5
        self.outfile = open("reV_{0}".format(filename), "wb")
        self.seqnums = {}  # single instance of each seqno

    def ack(self, seqno, data):
        res_data = []
        if (seqno == self.current_seqno) and len(self.seqnums) <= self.max_buf_size:
            self.seqnums[seqno] = data
            self.current_seqno += len(data)
            res_data.append(self.seqnums[seqno])
            del self.seqnums[seqno]
            self.updated = time.time()
            # return seqno of the last packet received
            return [((self.current_seqno - len(data)), res_data)]

        elif (seqno < self.current_seqno):
            self.updated = time.time()
            return [(seqno, res_data)]

        elif(seqno > self.current_seqno) and len(self.seqnums) < self.max_buf_size:
            self.updated = time.time()
            self.seqnums[seqno] = data
            return []


    def record(self, data):
        self.outfile.write(data)
        self.outfile.flush()
        self.updated = time.time()

    def end(self):
        self.outfile.close()
