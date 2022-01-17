#!/usr/bin/env python3

"""
A Python program to read a file containing ADS-B transponder messages
from aircraft, with timestamps, and turn them into music.
"""

import argparse
import datetime
import pygame.midi
import time

DEFAULT_UPDATE_INTERVAL = 10.0  # seconds
MAX_DISTANCE = 70000
MIDI_VOLUME_MAX = 100

class FilePlayer(object):
    def __init__(self, args):
        self._mylat = args.lat
        self._mylon = args.lon
        self._midi_channels = range(args.midi_channels)  # 0-based
        self._file = args.file
        self._player = None
        self._min_altitude = args.min_altitude
        self._max_altitude = args.max_altitude

    def init(self):
        if not pygame.midi.get_init():
            pygame.midi.init()
        id = 0
        while True:
            devinf = pygame.midi.get_device_info(id)
            if devinf is not None:
                (interf, name, input, output, opened) = devinf
                if "IAC" in name.decode("utf-8") and output == 1:
                    print("Using device id %d" % id)
                    break
            else:
                sys.stderr.write("Can't find IAC output\n")
                sys.exit(1)
            id += 1
        self._player = pygame.midi.Output(id)  # TODO(ggood) hardcoded device
        i = 0
        for channel in self._midi_channels:
            # Set instrument <n> to MIDI channel <n>
            self._player.set_instrument(i, channel)
            i += 1

    def all_notes_off(self):
        for midi_channel in self._midi_channels:
            for i in range(127):
                self._player.note_off(i, channel=midi_channel)

    def play(self):
        print("play from %s" % self._file)
        with open(self._file, "r") as fp:
            for line in fp:
                print(line.rstrip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, help="Your latitude",
                        required=True)
    parser.add_argument("--lon", type=float, help="Your longitude",
                        required=True)
    parser.add_argument("--midi-channels", type=int,
                         help="Number of MIDI channels to use",
                         default=1)
    parser.add_argument("--min_altitude", type=int,
                         help="Ignore aircraft lower than this altitude (feet)",
                         default=0)
    parser.add_argument("--max_altitude", type=int,
                         help="Ignore aircraft higher than this altitude (feet)",
                         default=100000)
    parser.add_argument("-f", "--file", type=str,
                        help="File to read aircraft data from",
                        required=True)

    args = parser.parse_args()

    file_player = FilePlayer(args)
    file_player.init()
    file_player.play()


if __name__ == "__main__":
    main()
