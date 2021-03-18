#!/usr/bin/env python

import argparse
import math
import random
import socket
import sys
import time

import pygame.midi

pygame.midi.init()
player = pygame.midi.Output(1)
player.set_instrument(0)

EARTH_RADIUS = 6371000

PURGE_TIME = 10

UPDATE_INTERVAL = 30.0  # seconds
last_update = 0.0

MAX_ALTITUDE = 40000
MAX_DISTANCE = 70000 
MIDI_VOLUME_MAX = 100
MAX_VOICES = 8

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

all_aircraft = {}  # Maps ADSB ID -> aircraft info

def distance(lat1, lon1, lat2, lon2):
    # Calcuate distance between two points on the earth
    d_lat = math.radians(lat2-lat1)
    d_lon = math.radians(lon2-lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    a = (math.sin(d_lat/2) * math.sin(d_lat/2) +
         math.sin(d_lon/2) * math.sin(d_lon/2) *
         math.cos(lat1_rad) * math.cos(lat2_rad))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
    d = EARTH_RADIUS * c;
    return d

def bearing(lat1, lon1, lat2, lon2):
    # Calcuate bearing from (lat1, lon1) to (lat2, lon2)
    lat1_rad = math.radians(lat1)
    long1_rad = math.radians(lon1)
    lat_rad = math.radians(lat2)
    long2_rad = math.radians(lon2)

    d_lon = long2_rad - long1_rad

    d_phi = math.log(
        math.tan(lat_rad/2.0+math.pi/4.0)/math.tan(lat1_rad/2.0+math.pi/4.0))
    if abs(d_lon) > math.pi:
         if d_lon > 0.0:
             d_lon = -(2.0 * math.pi - dLong)
         else:
             d_lon = (2.0 * math.pi + dLong)

    bearing = (math.degrees(math.atan2(d_lon, d_phi)) + 360.0) % 360.0;
    return bearing

def print_sound_distance():
    global last_update
    if time.time() < last_update + UPDATE_INTERVAL:
        return
    last_update = time.time()
    print("%d aircraft" % len(all_aircraft))
    for i in range(127):
        player.note_off(i)
    voices = 0
    max_voices = random.randint(1, MAX_VOICES)
    for a in sorted(all_aircraft.values(), key=lambda x: x["distance"]):
        if a["distance"] > MAX_DISTANCE or a["altitude"] > MAX_ALTITUDE:
            continue
        if voices > max_voices:
            print("There are %d voices max %d, bailing" % (voices, max_voices))
            break
        voices += 1
        note_index = int(float(a["altitude"]) / MAX_ALTITUDE * MAX_MIDI_NOTE)
        note = MIDI_NOTE_PALETTE[note_index]
        volume = int((MAX_DISTANCE - a["distance"]) / MAX_DISTANCE * MIDI_VOLUME_MAX)
        player.note_on(note, volume)
        print("Alt %s note %d Dist %s Volume %d" % (a["altitude"], note, a["distance"], volume))


def map(x, in_min, in_max, out_min, out_max):
    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)


LED_COUNT = 60
def process_line(line, mylat, mylon):
    global all_aircraft

    parts = line.split(",")
    if parts and (parts[0] == "MSG"):
        if parts[1] == "3":
            # Airborne position message
            try:
                aircraft_id = parts[4]
                try:
                    altitude = int(parts[11])
                    lat = float(parts[14])
                    lon = float(parts[15])
                except ValueError:
                    return
                d = distance(lat, lon, mylat, mylon)
                b = bearing(mylat, mylon, lat, lon)
                if aircraft_id not in all_aircraft:
                    # New plane
                    aircraft = {
                        "id": aircraft_id,
                        "altitude": altitude,
                        "lat": lat,
                        "lon": lon,
                        "distance": d,
                        "bearing": b,
                        "update": time.time(),
                    }
                else:
                    # Update existing
                    aircraft = all_aircraft[aircraft_id]
                    aircraft.update({
                        "altitude": altitude,
                        "lat": lat,
                        "lon": lon,
                        "distance": d,
                        "bearing": b,
                        "update": time.time(),
                    })
                    
                all_aircraft[aircraft_id] = aircraft
                # Adjust update rate based on number of aircraft
                for id, aircraft in all_aircraft.items():
                    print_sound_distance()
                # Purge things we haven't seen in 10 minutes
                for id, aircraft in all_aircraft.items():
                    if aircraft["update"] < time.time() - PURGE_TIME:
                        del all_aircraft[id]
                        print "Purged aircraft %s" % id
            except:
                raise
                #sys.stderr.write("Ignored %s" % line)

def theremin(host, port, mylat, mylon):
    print "Connect to %s:%d" % (host, port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    fp = sock.makefile()
    try:
        while True:
            line = fp.readline()
            process_line(line, mylat, mylon)
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