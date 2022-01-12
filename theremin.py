#!/usr/bin/env python3

import argparse
import datetime
import pygame.midi
import socket
import sys
import time

import aircraft_map
import palettes

DEFAULT_UPDATE_INTERVAL = 10.0  # seconds
MAX_DISTANCE = 70000
MIDI_VOLUME_MAX = 100


def map_int(x, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min);


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
    else:
        return map_int(bearing, 180, 360, 0, 127)


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

    def make_sound(self):
        print("Rendering sound with palette %d offset %d" % (self._palette_index, self._palette_offset))
        palette = [note + self._palette_offset for note in self._palette]

        print("%s: %d aircraft" %
              (datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
               self._map.count()))

        self.all_notes_off()
        aircraft = self._map.closest(
            self._polyphony, min_altitude=self._min_altitude,
            max_altitude=self._max_altitude)
        midi_channel = 0
        for a in aircraft:
            if (a.distance_to(self._mylat, self._mylon) > MAX_DISTANCE or
                a.altitude > self._max_altitude):
                continue
            if (a.altitude < self._min_altitude):
                continue
            note_index = int(float(a.altitude) / self._max_altitude * len(palette))
            note = palette[note_index]
            volume = int((MAX_DISTANCE -
                          a.distance_to(self._mylat, self._mylon)) /
                          MAX_DISTANCE * MIDI_VOLUME_MAX)
            deg = a.bearing_from(self._mylat, self._mylon)
            pan_value = map_bearing_to_pan(deg)
            print("XXXX pan channel %d to %d" % (midi_channel, pan_value))
            set_pan(self._player, pan_value, midi_channel)
            self._player.note_on(note, volume, midi_channel)
            print("Id %s alt %s MIDI note %d MIDI vol %d MIDI chan %d "
                  "dist %d m" %
                  (a.id, a.altitude, note, volume, midi_channel + 1,
                   a.distance_to(self._mylat, self._mylon)))
            midi_channel = (midi_channel + 1) % self._num_midi_channels
        self._palette_index = (self._palette_index + 1) % len(self._all_palettes)
        self._palette = self._all_palettes[self._palette_index]
        self._palette_offset = (self._palette_offset + self._shift) % 12
        print("")


    def play(self):
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
                    if time.time() - prime_start > 3.0:
                        break
                    line = fp.readline()
                    self._map.update(line)
                print("Done.")
                last_midi_update = 0.0
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
                    self._map.update(line)
                    if time.time() - last_midi_update > self._update_interval:
                        self.make_sound()
                        last_midi_update = time.time()
        finally:
            sock.close()
            self.all_notes_off()
            pygame.midi.quit()


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
    parser.add_argument("--update_interval", type=int,
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
