#!/usr/bin/env python3

import argparse
import datetime
import socket
import sys
import time

class ADSBCapture(object):
    def __init__(self, args):
        self._host = args.host
        self._port = args.port
        self._file = args.file
        self._time = args.time
        self._end_time = time.time() + args.time

    def init(self):
        pass

    def capture(self):
        print("Connect to %s:%d" % (self._host, self._port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, self._port))
        fp = sock.makefile()
        with open(self._file, "w") as outfile:
            try:
                while True:
                    line = fp.readline()
                    if time.time() > self._end_time:
                        break
                    outfile.write("%f %s" % (time.time(), line))
            finally:
                sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="IP address or hostname of host running dump1090",
                        required=True)
    parser.add_argument("-p", "--port", type=int,
                        help="Port for dump1090 server",
                        required=True)
    parser.add_argument("-t", "--time", type=int,
                        help="Time (in seconds) of data to capture",
                        default=10)
    parser.add_argument("-f", "--file", type=str,
                        help="File to write",
                        required=True)

    args = parser.parse_args()

    capture = ADSBCapture(args)
    capture.init()
    capture.capture()


if __name__ == "__main__":
    main()
