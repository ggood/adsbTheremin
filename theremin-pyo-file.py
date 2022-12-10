#!/usr/bin/env python3

"""
A Python program to read a file of capured ADSB airplane position
data and turn it into music.
"""

import argparse
import datetime
import pickle
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

class FilePlayerTheremin(object):
    def __init__(self, args):
        self._mylat = args.lat
        self._mylon = args.lon
        self._polyphony = args.polyphony
        self._min_altitude = args.min_altitude
        self._max_altitude = args.max_altitude
        self._input_file = args.input_file
        self._playback_factor = args.playback_factor
        self._synthetic_now = 0.0
        self._map = None
        self._num_midi_channels = 8
        self._recorded_data = []
        self._real_start_time = 0.0
        self._synthetic_start_time = 0.0
        self._synthetic_now = 0.0
        self._current_aircraft = {}
        self._server = pyo.Server().boot().start()
        self._oscs = []
        self._shutdown_requested = False
        self._playback_index = 0

    def init(self):
        with open(self._input_file, "rb") as fp:
            self._recorded_data = pickle.load(fp)
        self._synthetic_start_time = self._recorded_data[0][0]
        self._synthetic_now = self._synthetic_start_time
        self._map = aircraft_map.AircraftMap(self._mylat, self._mylon,
                                             start_time=self._synthetic_now)
        self._real_start_time = time.time()
        print("Read %d entries starting at %f" % (
              len(self._recorded_data), self._real_start_time))
        for i in range(self._polyphony):
            #self._oscs.append(pyo.RCOsc(freq=[100, 100], mul=0).out())
            self._oscs.append(pyo.Sine(freq=[100, 100], mul=0).out())

    def map_frequency(self, aircraft):
        # TODO: make this more flexible, allow mapping to a set
        # of pitches rather than continuous
        freq = map_int(aircraft.altitude, self._min_altitude,
                       self._max_altitude, 20, 1200)
        return freq

    def play(self):
        nearest = self._map.closest(self._polyphony,
                                    min_altitude=self._min_altitude,
                                    max_altitude=self._max_altitude)

        def _advance_time():
            if self._playback_index > len(self._recorded_data) - 1:
                self._server.closeGui()
                return
            # Compute new synthetic time
            real_time_offset = time.time() - self._real_start_time
            synthetic_time_offset = real_time_offset * self._playback_factor
            print("index: %d real_time_offset %d synthetic_time_offset %d" % (self._playback_index, real_time_offset, synthetic_time_offset))
            self._synthetic_now = (self._synthetic_start_time +
                                   real_time_offset *
                                   self._playback_factor)
            # Send updates to aircraft map up until current synthetic time
            while True:
                self._map.update(
                    self._recorded_data[self._playback_index],
                    now=self._synthetic_now)
                self._playback_index += 1
                if self._playback_index > len(self._recorded_data) - 1:
                    break
                next_time = self._recorded_data[self._playback_index][0]
                if next_time > self._synthetic_now:
                    break

        def _make_sound():
            to_remove = []
            for aircraft_id, aircraft in list(self._current_aircraft.items()):
                if self._map.get(aircraft_id) is None:
                    print("lost %s" % aircraft_id)
                    to_remove.append(aircraft_id)
                if (aircraft.altitude <= self._min_altitude or
                        aircraft.altitude >= self._max_altitude):
                    print("aircraft %s busted altitude limits" % aircraft_id)
                    to_remove.append(aircraft_id)
            for aircraft_id in to_remove:
                del(self._current_aircraft[aircraft_id])
            if len(self._current_aircraft) < self._polyphony:
                # Add more
                closest = self._map.closest(self._polyphony,
                                            min_altitude=self._min_altitude,
                                            max_altitude=self._max_altitude)
                for aircraft in closest:
                    if aircraft.id not in self._current_aircraft:
                        self._current_aircraft[aircraft.id] = aircraft
                        print("Added %s" % aircraft.id)
                        break
            osc_index = 0
            for aircraft_id, aircraft in list(self._current_aircraft.items()):
                # Set volume
                dist = aircraft.distance_to(self._mylat, self._mylon)
                vol = map_int(dist, 0, 10000, 0, 100)
                vol = vol / 100.0
                # Set frequency
                freq = self.map_frequency(aircraft)
                self._oscs[osc_index].vol = vol
                self._oscs[osc_index].freq = freq
                print("%d: %s %f Hz vol %f for alt %s" % (osc_index, aircraft.id, freq, vol, aircraft.altitude))
                self._oscs[osc_index].mul = 0.01
                osc_index += 1

        time_pat = pyo.Pattern(function=_advance_time, time=0.1).play()
        play_pat = pyo.Pattern(function=_make_sound, time=0.1).play()
        self._server.gui()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, help="Your latitude",
                        required=True)
    parser.add_argument("--lon", type=float, help="Your longitude",
                        required=True)
    parser.add_argument("--polyphony", type=int,
                        help="Number of simultaneous notes",
                        default=8)
    parser.add_argument("--min-altitude", type=int,
                         help="Ignore aircraft lower than this altitude (feet)",
                         default=0)
    parser.add_argument("--max-altitude", type=int,
                         help="Ignore aircraft higher than this altitude (feet)",
                         default=100000)
    parser.add_argument("--input-file",
                        help="Input file to read", required=True)
    parser.add_argument("--playback-factor", type=float,
                        help="Playback factor - how many times to speed up time",
                        default=10)

    args = parser.parse_args()

    adsb_theremin = FilePlayerTheremin(args)
    adsb_theremin.init()
    adsb_theremin.play()


if __name__ == "__main__":
    main()
