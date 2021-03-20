#!/usr/bin/env python

import argparse
import socket
import sys
import time

import aircraft_map

UPDATE_INTERVAL = 5
def make_sound(aircraft):
    pass

def theremin(host, port, mylat, mylon):
    last_midi_update = time.time()
    map = aircraft_map.AircraftMap(mylat, mylon)
    print "Connect to %s:%d" % (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    fp = sock.makefile()
    try:
        while True:
            line = fp.readline()
            map.update(line)
            if time.time() - last_midi_update > UPDATE_INTERVAL:
                make_sound(map.closest(3))
                last_midi_update = time.time()
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

    args = parser.parse_args()

    theremin(args.host, args.port, args.lat, args.lon)


if __name__ == "__main__":
    main()
