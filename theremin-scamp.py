#!/usr/bin/env python3.9

"""
A Python program to read ADS-B transponder messages from aircraft
and turn then into music. Uses SCAMP (Suite for Computer-Assisted
Music in Python - https://scamp.marcevanstein.com/)
"""

import argparse
import datetime
import socket
import sys
import time

import aircraft_map
import palettes
import util

import scamp


DEFAULT_UPDATE_INTERVAL = 10

class ADSBTheremin(object):
    def __init__(self, args):
        self._host = args.host
        self._port = args.port
        self._mylat = args.lat
        self._mylon = args.lon
        self._midi_channels = range(args.midi_channels)  # 0-based
        self._num_midi_channels = len(self._midi_channels)
        self._polyphony = args.polyphony
        self._update_interval = args.update_interval
        self._player = None
        self._all_palettes = palettes.MIDI_NOTE_PALETTES
        self._palette_index = 0
        self._palette = self._all_palettes[self._palette_index]
        self._shift = args.shift
        self._palette_offset = 0
        self._min_altitude = args.min_altitude
        self._max_altitude = args.max_altitude
        self._map = aircraft_map.AircraftMap(args.lat, args.lon)
        self._announcer_instrument = None
        self._session = None

    def init(self):
        # TODO(ggood) init scamp here
        self._session = scamp.Session()
        self._announcer_instrument = self._session.new_part("Vibraphone")
        self._map.register_callback("Updater", self)

    def all_notes_off(self):
        pass  # TODO(can scamp do this?)

    def new_aircraft_callback(self, aircraft):
        print("New aircraft %s detected altitude %d distance %d" %
              (aircraft.id, aircraft.altitude,
               aircraft.distance_to(self._mylat, self._mylon)))
        # TODO "announce" the new aircraft with a percussive
        # pitched sound like a vibraphone, piano, marimba...
        # Also begin a long-lived tone on a sustained instrument
        # like a string instrument. The pitch is determined by
        # the aircraft altitude, and the volume is determined
        # by the distance to the aircraft.
        midi_note = self.altitude_to_midi_note(aircraft)
        volume = self.distance_to_volume(aircraft)
        self._announcer_instrument.play_note(midi_note, volume, 1.0, blocking=False)

    def update_aircraft_callback(self, aircraft):
        print("Position update for aircraft %s" % aircraft.id)
        # TODO: re-determine the pitch based on the altitude
        # and if it's different, play a note of the new pitch.

    def remove_aircraft_callback(self, aircraft):
        print("Removal of aircraft %s" % aircraft.id)
        # TODO remove the instrument from the ensemble

    def altitude_to_midi_note(self, aircraft):
        """Given an aircraft, map its altitude to a MIDI note"""
        # TODO(ggood) for now, this is a simple linear map.
        # In the future, get this from some object that produces
        # notes in some particular tonality, and arrange for the
        # tonalities it uses to evolve over time.
        if not self.altitude_in_range(aircraft):
            return
        midi_note = util.map_int(aircraft.altitude, self._min_altitude,
                                  self._max_altitude, 32, 110)  # XXX(ggood) fix hardcoded
        print("MIDI note %d" % midi_note)
        return midi_note

    def distance_to_volume(self, aircraft):
        """Given an aircraft, map its distance to a volume 0.0-1.0.
        Constrain especially large distances to a maximum."""
        distance = aircraft.distance_to(self._mylat, self._mylon)
        print("XXXX distance %d" % distance)
        volume = util.map_int(
            util.constrain(distance, 0, 50000), 50000, 0, 10, 100) / 100.0
        print("Volume %f" % volume)
        return volume

    def altitude_in_range(self, aircraft):
        return (aircraft.altitude >= self._min_altitude and
                aircraft.altitude <= self._max_altitude)

    def play(self):
        # Main loop - read ADSB position data from TCP socket (or, in
        # the future, a file of timestamped data). Feed each line
        # to the aircraft_map, which keeps track of all the aircraft
        # and their positions, and will call us back (via update_callback(),
        # above) when a change in an aircraft's position or altitude
        # is detected.
        try:
            cont = True
            while True:
                if not cont:
                    # Something other than a lost connection happened, so bail
                    break
                print("Connect to %s:%d" % (self._host, self._port))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self._host, self._port))
                fp = sock.makefile()
                cont = False
                while True:
                    line = fp.readline()
                    if len(line) == 0:
                        # This seems to happen sometimes, we need to reconnect
                        print("No data, reconnect")
                        cont = True
                        sock.close()
                        self.all_notes_off()
                        break
                    self._map.update_from_raw(line)
        finally:
            sock.close()
            self.all_notes_off()


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
    parser.add_argument("--update-interval", type=float,
                        help="Update interval in seconds",
                        default=DEFAULT_UPDATE_INTERVAL)
    parser.add_argument("--shift", type=int,
                        help="Semitones offset per palette change",
                        default=0)
    parser.add_argument("--min-altitude", type=int,
                         help="Ignore aircraft lower than this altitude (feet)",
                         default=0)
    parser.add_argument("--max-altitude", type=int,
                         help="Ignore aircraft higher than this altitude (feet)",
                         default=100000)

    args = parser.parse_args()

    adsb_theremin = ADSBTheremin(args)
    adsb_theremin.init()
    adsb_theremin.play()


if __name__ == "__main__":
    main()
