#!/usr/bin/env python

import argparse
import datetime
import socket
import sys
import time

import aircraft_map

import pygame.midi

pygame.midi.init()
player = pygame.midi.Output(1)
player.set_instrument(0)

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



def theremin(host, port, mylat, mylon):
    map = aircraft_map.AircraftMap(mylat, mylon)
    print("Connect to %s:%d" % (host, port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
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
                make_sound(map.closest(8), mylat, mylon)
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
