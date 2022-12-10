#!/usr/bin/env python3

"""
A Python program to read ADS-B transponder messages from aircraft
and save them for later playback
"""

import argparse
import datetime
import pickle
import signal
import socket
import sys
import time

import aircraft_map

def sigint_handler(signum, frame):
    global adsb_recorder
    adsb_recorder.stop()

signal.signal(signal.SIGINT, sigint_handler)

class ADSBRecorder(object):
    def __init__(self, args):
        self._host = args.host
        self._port = args.port
        self._input_file = args.input_file
        self._mylat = args.lat
        self._mylon = args.lon
        self._output_filename = args.output_file
        self._output_file = open(args.output_file, "wb")
        self._duration = args.duration
        if self._duration is None:
            self._stop_time = sys.float_info.max
        else:
            self._stop_time = time.time() + self._duration
        self._map = aircraft_map.AircraftMap(args.lat, args.lon,
                                             position_accuracy=1)
        self._stop_requested = False

    def _get_fp(self):
        if self._input_file is not None:
            print("reading from file %s" % self._input_file)
            fp = open(self._input_file, "r")
            return fp, None
        else:
            print("Connect to %s:%d" % (self._host, self._port))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._host, self._port))
            fp = sock.makefile()
            return fp, sock

    def record(self):
        recorded_data = []
        try:
            cont = True
            while True:
                if not cont:
                    break
                fp, sock = self._get_fp()
                cont = False
                while not self._stop_requested:
                    if time.time() > self._stop_time:
                        print("Now %s is after stop time %s" % (time.time(), self._stop_time))
                        break
                    line = fp.readline()
                    if (len(line) == 0) and (sock is not None):
                        # This seems to happen sometimes, we need to reconnect
                        # if connected over a socket
                        print("No data, reconnect")
                        cont = True
                        break
                    (updated, aircraft) = self._map.update_from_raw(line)
                    if aircraft is not None:
                        if updated:
                            print("%s, %d aircraft" %
                                  (aircraft.id, self._map.count()))
                    if updated:
                        recorded_data.append(
                            [time.time(), aircraft.id, aircraft.altitude,
                             aircraft.latitude, aircraft.longitude])
        except ConnectionResetError:
            pass  # ignore and continue
        finally:
            if sock is not None:
                sock.close()
            if fp is not None:
                fp.close()
            pickle.dump(recorded_data, self._output_file)
            self._output_file.close()
            print("%d records written to %s" % (
                len(recorded_data), self._output_filename))

    def stop(self):
        self._stop_requested = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="IP address or hostname of host running dump1090")
    parser.add_argument("-p", "--port", type=int,
                        help="Port for dump1090 server")
    parser.add_argument("--input-file",
                        help="Filename to read from")
    parser.add_argument("--lat", type=float, help="Your latitude",
                        required=True)
    parser.add_argument("--lon", type=float, help="Your longitude",
                        required=True)
    parser.add_argument("--output-file",
                        help="Filename to write recorded data to",
                        required=True)
    parser.add_argument("-d", "--duration", type=int,
                        help="Run time in seconds")

    args = parser.parse_args()

    if not((args.host is not None and args.port is not None) or
            args.input_file is not None):
        sys.stderr.write("Either input-file or host and port are required\n")
        sys.exit(1)

    global adsb_recorder
    adsb_recorder = ADSBRecorder(args)
    adsb_recorder.record()


if __name__ == "__main__":
    main()
