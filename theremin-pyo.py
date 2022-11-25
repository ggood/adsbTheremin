#!/usr/bin/env python3

"""
A Python program to read ADS-B transponder messages from aircraft
and turn then into music.
"""

import argparse
import datetime
import socket
import sys
import time

import pyo

import aircraft_map
import palettes

DEFAULT_UPDATE_INTERVAL = 10.0  # seconds
MAX_DISTANCE = 70000
MIDI_VOLUME_MAX = 100


def map_int(x_coord, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return int((x_coord - in_min) * (out_max - out_min) /
               (in_max - in_min) + out_min)


def set_pan(player, pan, channel):
    """
    Set the panning on a MIDI channel. 0 = hard left, 127 = hard right.
    """
    status = 0xb0 | channel
    player.write_short(status, 0x0a, pan)


def map_bearing_to_pan(bearing):
    """
    Convert a plane's bearing to a MIDI pan controller value.
    """
    bearing = (int(bearing) + 270) % 360
    if bearing < 180:
        return map_int(bearing, 0, 180, 127, 0)
    return map_int(bearing, 180, 360, 0, 127)


class ADSBTheremin(object):
    def __init__(self, args):
        self._host = args.host
        self._port = args.port
        self._mylat = args.lat
        self._mylon = args.lon
        self._polyphony = args.polyphony
        self._update_interval = args.update_interval
        self._all_palettes = palettes.MIDI_NOTE_PALETTES
        self._palette_index = 0
        self._palette = self._all_palettes[self._palette_index]
        self._shift = args.shift
        self._palette_offset = 0
        self._min_altitude = args.min_altitude
        self._max_altitude = args.max_altitude
        self._map = aircraft_map.AircraftMap(args.lat, args.lon)
        self._num_midi_channels = 8
        self._server = pyo.Server().boot().start()
        self._oscs = []

    def init(self):
        for i in range(self._polyphony):
            self._oscs.append(pyo.RCOsc(freq=[100, 100], mul=0).out())

    def make_sound(self):
        print("Rendering sound with palette %d offset %d" %
              (self._palette_index, self._palette_offset))
        palette = [note + self._palette_offset for note in self._palette]

        print("%s: %d aircraft" %
              (datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
               self._map.count()))

        aircraft = self._map.closest(
            self._polyphony, min_altitude=self._min_altitude,
            max_altitude=self._max_altitude)
        midi_channel = 0
        osc_index = 0
        for a in aircraft:
            if (a.distance_to(self._mylat, self._mylon) > MAX_DISTANCE or
                a.altitude > self._max_altitude):
                print("ignoring %s" % a)
                continue
            if a.altitude < self._min_altitude:
                print("ignoring %s" % a)
                continue
            note_index = int(float(a.altitude - 1) / self._max_altitude * len(palette))

            note = palette[note_index]
            volume = int((MAX_DISTANCE -
                          a.distance_to(self._mylat, self._mylon)) /
                          MAX_DISTANCE * MIDI_VOLUME_MAX)
            deg = a.bearing_from(self._mylat, self._mylon)
            pan_value = map_bearing_to_pan(deg)
            print("Id %s alt %s MIDI note %d MIDI vol %d MIDI chan %d "
                  "dist %d m" %
                  (a.id, a.altitude, note, volume, midi_channel + 1,
                   a.distance_to(self._mylat, self._mylon)))
            freq = pyo.midiToHz(note)
            print(freq)
            self._oscs[osc_index].freq = freq
            self._oscs[osc_index].mul = 0.1
            midi_channel = (midi_channel + 1) % self._num_midi_channels
            osc_index += 1
        self._palette_index = (self._palette_index + 1) % len(self._all_palettes)
        self._palette = self._all_palettes[self._palette_index]
        self._palette_offset = (self._palette_offset + self._shift) % 12
        print("")

    def play(self):
        def _collect():
            # TODO - loop and read all available lines. This
            # might get behind if not called often enough.
            line = fp.readline()
            self._map.update(line)

        try:
            cont = True
            while True:
                if not cont:
                    break
                print("Connect to %s:%d" % (self._host, self._port))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self._host, self._port))
                fp = sock.makefile()
                # Prime the aircraft list - just get updates for a little while
                print("Priming aircraft map...")
                prime_start = time.time()
                while True:
                    if time.time() - prime_start > 3.0:  # XXX FIX
                        break
                    line = fp.readline()
                    self._map.update(line)
                print("Done.")
                break
            print("Starting pattern")
            collect_pat = pyo.Pattern(function=_collect, time=0.1).play()
            make_sound_pat = pyo.Pattern(function=self.make_sound, time=10).play()
            #self._server.start()
            self._server.gui()
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
    parser.add_argument("--update_interval", type=float,
                        help="Update interval in seconds",
                        default=DEFAULT_UPDATE_INTERVAL)
    parser.add_argument("--shift", type=int,
                        help="Semitones offset per palette change",
                        default=0)
    parser.add_argument("--min_altitude", type=int,
                         help="Ignore aircraft lower than this altitude (feet)",
                         default=0)
    parser.add_argument("--max_altitude", type=int,
                         help="Ignore aircraft higher than this altitude (feet)",
                         default=100000)

    args = parser.parse_args()

    adsb_theremin = ADSBTheremin(args)
    adsb_theremin.init()
    adsb_theremin.play()


if __name__ == "__main__":
    main()
