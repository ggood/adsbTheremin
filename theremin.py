#!/usr/bin/env python

import argparse
import datetime
import socket
import sys
import time

import aircraft_map

import pygame.midi

pygame.midi.init()
#player = pygame.midi.Output(1)
#player.set_instrument(0)

UPDATE_INTERVAL = 30.0  # seconds
MAX_VOICES = 8
MAX_ALTITUDE = 40000
MAX_DISTANCE = 70000
MIDI_VOLUME_MAX = 100

MIDI_NOTE_PALETTE = (
24,
36,
48, 50, 53, 55, 58,
60, 62, 65, 67, 70,
72, 74, 77, 79, 82,
84, 86, 89, 91, 94,
106, 108, 111, 113, 116,
118, 120, 123
)

MAX_MIDI_NOTE = len(MIDI_NOTE_PALETTE)

def make_sound(aircraft, mylat, mylon):
    print(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    for i in range(127):
        player.note_off(i)
    for a in aircraft:
        if a.distance_to(mylat, mylon) > MAX_DISTANCE or a.altitude > MAX_ALTITUDE:
            continue
        note_index = int(float(a.altitude) / MAX_ALTITUDE * MAX_MIDI_NOTE)
        note = MIDI_NOTE_PALETTE[note_index]
        volume = int((MAX_DISTANCE - a.distance_to(mylat, mylon)) / MAX_DISTANCE * MIDI_VOLUME_MAX)
        player.note_on(note, volume)
        print("Id %s alt %s MIDI note %d MIDI vol %d dist %d m" %
            (a.id, a.altitude, note, volume, a.distance_to(mylat, mylon)))
    print("")



def theremin(args):
    map = aircraft_map.AircraftMap(args.lat, args.lon)
    print("Connect to %s:%d" % (args.host, args.port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))
    fp = sock.makefile()
    try:
        # Prime the aircraft list - just get updates for a little while
        print("Priming aircraft map...")
        prime_start = time.time()
        while True:
            if time.time() - prime_start > 3.0:
                break
            line = fp.readline()
            map.update(line)
        print("Done.")
        last_midi_update = 0.0
        while True:
            line = fp.readline()
            map.update(line)
            if time.time() - last_midi_update > UPDATE_INTERVAL:
                make_sound(map.closest(8), args.lat, args.lon)
                last_midi_update = time.time()
    finally:
        sock.close()


def map_int(x, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


def set_pan(pan, channel):
    """
    Set the panning on a MIDI channel. 0 = hard left, 127 = hard right.
    """
    status = 0xb0 | channel
    player.write_short(status, 0x0a, pan)


def map_bearing_to_pan(bearing):
    """
    Convert a plane's bearing to a MIDI pan controller value.
    """
    bearing = (bearing + 270) % 360
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
        self._player = None
        self._map = aircraft_map.AircraftMap(args.lat, args.lon)

    def init(self):
        if not pygame.midi.get_init():
            pygame.midi.init()
        self._player = pygame.midi.Output(1)  # TODO(ggood) hardcoded device
        i = 0
        for channel in self._midi_channels:
            # Set instrument <n> to MIDI channel <n>
            self._player.set_instrument(i, channel)
            i += 1

    def make_sound(self):
        print(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

        # All notes off
        for midi_channel in self._midi_channels:
            for i in range(127):
                self._player.note_off(i, channel=channel)

        aircraft = self._map.closest(8)  # TODO(ggood) hardcoded 8
        midi_channel_index = 0
        for a in aircraft:
            if (a.distance_to(mylat, mylon) > MAX_DISTANCE or
                a.altitude > MAX_ALTITUDE):
                continue
            note_index = int(float(a.altitude) / MAX_ALTITUDE * MAX_MIDI_NOTE)
            note = MIDI_NOTE_PALETTE[note_index]
            volume = int((MAX_DISTANCE - a.distance_to(mylat, mylon)) /
                          MAX_DISTANCE * MIDI_VOLUME_MAX)
            channel = self._midi_channels[midi_channel_offset]
            self._player.note_on(note, volume, channel)
            print("Id %s alt %s MIDI note %d MIDI vol MIDI chan %s "
                  "%d dist %d m" %
                  (a.id, a.altitude, note, volume, channel,
                   a.distance_to(mylat, mylon)))
            midi_channel_offset = (midi_channel_offset + 1) %
                                   self._num_midi_channels
        print("")


    def play(self):
        print("Connect to %s:%d" % (self._host, self._port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, self._port))
        fp = sock.makefile()
        try:
            # Prime the aircraft list - just get updates for a little while
            print("Priming aircraft map...")
            prime_start = time.time()
            while True:
                if time.time() - prime_start > 3.0:
                    break
                line = fp.readline()
                map.update(line)
            print("Done. Seeing %d aircraft" % map.count())
            last_midi_update = 0.0
            while True:
                line = fp.readline()
                map.update(line)
                if time.time() - last_midi_update > UPDATE_INTERVAL:
                    self.make_sound()
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
    parser.add_argument("--midi-channels", type=int,
                         help="Number of MIDI channels to use",
                         default=1)

    args = parser.parse_args()

    adsb_theremin = ADSBTheremin(args)
    adsb_theremin.init()
    adsb_theremin.play()
    #theremin(args)


if __name__ == "__main__":
    main()
