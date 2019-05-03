import argparse

from Client import Client
from Server import Server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unicorn based magic for file transfer.",
                                     epilog="Unicorns powered this")
    parser.add_argument("-s", "--server", help="Run as server", action="store_true")
    parser.add_argument("-d", "--directory", help="Directory to read files from", default=".")
    parser.add_argument("-p", "--port", help="Local port to bind", type=int, default=3372)
    parser.add_argument("-rp", "--rport", help="Remote port to connect", type=int, default=3372)
    parser.add_argument("-a", "--address", help="Remote server address", default="localhost")
    args = parser.parse_args()

    if args.server:
        Server(args.port, args.directory).start()
    else:
        Client(args.address, args.rport, args.port).start()
