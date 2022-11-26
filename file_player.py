#!/usr/bin/env python3

"""
A Python program to read a file containing ADS-B transponder messages
from aircraft, with timestamps, and turn them into music.
"""

import argparse
import datetime
import pygame.midi
import re
import time

import aircraft_map
import palettes

DEFAULT_UPDATE_INTERVAL = 10.0  # seconds
MAX_DISTANCE = 70000
MIDI_VOLUME_MAX = 100
TIME_RE = re.compile("^([0-9\.][0-9\.]*) (.*)")

class FilePlayer(object):
    def __init__(self, args):
        self._mylat = args.lat
        self._mylon = args.lon
        self._midi_channels = range(args.midi_channels)  # 0-based
        self._file = args.file
        self._player = None
        self._min_altitude = args.min_altitude
        self._max_altitude = args.max_altitude
        self._map = aircraft_map.AircraftMap(args.lat, args.lon)
        self._all_palettes = palettes.MIDI_NOTE_PALETTES
        self._num_midi_channels = 8  # TODO(ggood) make configurable
        self._time_factor = args.time_factor

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
        palette = self._all_palettes[0]

        with open(self._file, "r") as fp:
            last_event_time = None
            for line in fp:
                self._map.update(line)
                g = TIME_RE.search(line)
                event_time = float(g.groups()[0])
                adsb_data = g.groups()[1]
                self._map.update(adsb_data)
                if last_event_time is not None:
                    time.sleep(self._time_factor * (event_time - last_event_time))
                last_event_time = event_time
                aircraft = self._map.closest(20)
                midi_channel = 0
                # This is wrong, I should just sonify each note as it is read, don't
                # even bother updating the aircraft map.
                for a in aircraft:
                    if (a.distance_to(self._mylat, self._mylon) > MAX_DISTANCE or
                        a.altitude > self._max_altitude):
                        continue
                    if a.altitude < self._min_altitude:
                        continue
                    note_index = int(float(a.altitude - 1) / self._max_altitude * len(palette))
                    note = palette[note_index]
                    volume = int((MAX_DISTANCE -
                                  a.distance_to(self._mylat, self._mylon)) /
                                  MAX_DISTANCE * MIDI_VOLUME_MAX)
                    self._player.note_on(note, volume, midi_channel)
                    print("Id %s alt %s MIDI note %d MIDI vol %d MIDI chan %d "
                          "dist %d m" %
                          (a.id, a.altitude, note, volume, midi_channel + 1,
                           a.distance_to(self._mylat, self._mylon)))
                    midi_channel = (midi_channel + 1) % self._num_midi_channels

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
    parser.add_argument("--time_factor", type=int,
                         help="Slow down playback by this factor",
                         default=1)

    args = parser.parse_args()

    file_player = FilePlayer(args)
    file_player.init()
    file_player.play()


if __name__ == "__main__":
    main()
