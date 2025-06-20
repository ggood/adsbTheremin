#!/usr/bin/env python3

"""
Reads a series of saved ADSB data  dump files, and serves them
to a TCP socket, as if being served by dump1090. Also allows
for playback to be sped up or slowed down.
"""

import argparse
import pickle
import socket
import time
import traceback

class SyntheticClock:
    def __init__(self, factor):
        self._factor = factor
        self._start_time = None

    def start(self):
        self._start_time = time.time()

    def now(self):
        return (time.time() - self._start_time) * self._factor

class FileSocketServer(object):
    def __init__(self, args):
        self._files = args.files
        self._time_factor = args.time_factor
        self._port = args.port
        self._data = []
        self._clock = SyntheticClock(self._time_factor)

    def init(self):
        all_file_data = []
        for file in self._files:
            try:
                file_data = pickle.load(open(file, "rb"))
                print("Loaded %d data points from file %s" % (len(file_data), file))
                all_file_data.extend(pickle.load(open(file, "rb")))
            except Exception as ex:
                print("oops on %s" % file)
                print(traceback.format_exc())
        print("Loaded %d data points" % len(all_file_data))
        self._data = sorted(all_file_data)

    def serve(self, connection):
        # Note the timestamp of the first data point
        first_timestamp = self._data[0][0]
        self._clock.start()
        for timestamp, line in self._data:
            time_offset = timestamp - first_timestamp
            clock_now = self._clock.now()
            if time_offset < clock_now:
                print("%0.2f %s" % (time_offset, line))
                connection.send(line.encode("utf-8"))
            else:
                sleep_time = (time_offset - clock_now) / self._time_factor
                time.sleep(sleep_time)
                print("%0.2f %s" % (time_offset, line))
                connection.send(line.encode("utf-8"))

    def wait_for_connection(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('localhost', self._port))
        serversocket.listen(5) # become a server socket, maximum 5 connections

        while True:
            connection, address = serversocket.accept()
            try:
                self.serve(connection)
            except Exception as ex:
                print(traceback.format_exc())
                # Client probably disconnected. Just go back to listening.

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int,
                         help="TCP listen port",
                         default=1)
    parser.add_argument("--time-factor", type=float,
                         help="Scale playback by this factor",
                         default=1)
    parser.add_argument("files", nargs="*")

    args = parser.parse_args()

    file_player = FileSocketServer(args)
    file_player.init()
    file_player.wait_for_connection()


if __name__ == "__main__":
    main()
