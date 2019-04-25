import time


class Connection:
    def __init__(self, host, port, start_seq, filename, debug=False):
        self.debug = debug
        self.updated = time.time()
        self.current_seqno = start_seq  # expect to ack from the start_seqno
        self.host = host
        self.port = port
        self.max_buf_size = 5
        self.outfile = open("out_{0}".format(filename), "wb")
        self.seqnums = {}  # enforce single instance of each seqno

    def ack(self, seqno, data):
        res_data = []
        self.updated = time.time()
        # if the sequence number of the received packet is larger than the current sequence number and
        # the window size is not exceeded
        if (seqno == self.current_seqno) and self.seqnums.__len__() <= self.max_buf_size:
            # Add the data to the window with the sequence number as the lookup value
            self.seqnums[seqno] = data
            # Then, for every sequence number
            for n in sorted(self.seqnums.keys()):
                # If the sequence number is equal to the one we need
                if n == self.current_seqno:
                    # "Receive" and rebuild the data and remove if from the window
                    self.current_seqno += len(data)
                    res_data.append(self.seqnums[n])
                    del self.seqnums[n]
                else:
                    break  # when we find out of order seqno, quit and move on

        if self.debug:
            print("next seqno should be %d" % self.current_seqno)

        # note: we return the sequence number of the last packet received
        return (self.current_seqno - len(data)), res_data

    def record(self, data):
        self.outfile.write(data)
        self.outfile.flush()

    def end(self):
        self.outfile.close()
