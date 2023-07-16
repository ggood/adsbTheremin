#!/usr/bin/env python3

import argparse
import datetime
import socket
import sys
import time

import aircraft_map

DEFAULT_UPDATE_INTERVAL = 10.0  # seconds
MIN_ALTITUDE = 3000
MAX_ALTITUDE = 40000
MAX_DISTANCE = 70000


def map_int(x, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min);


class MapDriver(object):
    def __init__(self, args):
        self._host = args.host
        self._port = args.port
        self._mylat = args.lat
        self._mylon = args.lon
        self._update_interval = args.update_interval
        self._map = aircraft_map.AircraftMap(args.lat, args.lon)

    def init(self):
        pass

    def make_sound(self):
        print("%s: %d aircraft" %
              (datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
               self._map.count()))

    def play(self):
        cont = True
        while True:
            if not cont:
                break
            cont = False
            print("Connect to %s:%d" % (self._host, self._port))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._host, self._port))
            fp = sock.makefile("rb", buffering=0)
            start_time = time.time()
            try:
                while True:
                    line = fp.readline()
                    print("%f: read %s" % (time.time() - start_time, line))
                    if len(line) == 0:
                        print("No data, restart")
                        cont = True
                        break
                    #self._map.update(line)
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
    parser.add_argument("--lat", type=float, help="Your latitude",
                        required=True)
    parser.add_argument("--lon", type=float, help="Your longitude",
                        required=True)
    parser.add_argument("--midi-channels", type=int,
                         help="Number of MIDI channels to use",
                         default=1)
    parser.add_argument("--polyphony", type=int,
                        help="Number of simultaneous notes",
                        default=8)
    parser.add_argument("--update-interval", type=int,
                        help="Update interval in seconds",
                        default=DEFAULT_UPDATE_INTERVAL)
    parser.add_argument("--shift", type=int,
                        help="Semitones offset per palette change",
                        default=0)

    args = parser.parse_args()

    map_driver = MapDriver(args)
    map_driver.init()
    map_driver.play()


if __name__ == "__main__":
    main()
