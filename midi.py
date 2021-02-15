#!/usr/bin/env python

import argparse
import colorsys
import math
import socket
import sys
import time

EARTH_RADIUS = 6371000

PURGE_TIME = 10

UPDATE_INTERVAL = 5.0  # seconds
last_update = time.time()

MAX_ALTITUDE = 40000
MAX_DISTANCE = 200000
MIDI_NOTES_COUNT = 127
MIDI_VOLUME_MAX = 127

all_aircraft = {}  # Maps ADSB ID -> aircraft info
next_slot = 0  # Which LED to use to show this aircraft

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

    d_phi = math.log(math.tan(lat_rad/2.0+math.pi/4.0)/math.tan(lat1_rad/2.0+math.pi/4.0))
    if abs(d_lon) > math.pi:
         if d_lon > 0.0:
             d_lon = -(2.0 * math.pi - dLong)
         else:
             d_lon = (2.0 * math.pi + dLong)

    bearing = (math.degrees(math.atan2(d_lon, d_phi)) + 360.0) % 360.0;
    return bearing

def get_color(aircraft):
    # Map aircraft position, etc to an LED color
    # Brightness = 255 when 0 m away, 0 when 100km away
    # Color = blue for now. Clamp at 100,000 meters
    if aircraft["distance"] < 100000:
        scaled_distance = 255 - int((aircraft["distance"] / 100000.0) * 255)
    else:
        scaled_distance = 255
    #print "distance %s -> %s = %s" % (aircraft["distance"], scaled_distance, RGB_ntuples[scaled_distance])
    return RGB_ntuples[255 - scaled_distance]
    #return Color(0, 0, scaled_distance )


def print_aircraft():
    print ""
    for a in sorted(all_aircraft.values(), key=lambda x: x["slot"]):
        print ("%d: id %s alt %5d lat %6.2f lon %6.2f dist %5.0f m "
               "bearing %0.0f deg" %
               (a["slot"], a["id"], a["altitude"], a["lat"], a["lon"],
                a["distance"], a["bearing"]))

def print_sound():
    global last_update
    if time.time() < last_update + UPDATE_INTERVAL:
        return
    last_update = time.time()
    print("%d aircraft" % len(all_aircraft))
    for a in sorted(all_aircraft.values(), key=lambda x: x["slot"]):
        note = a["altitude"] / MAX_ALTITUDE * MIDI_NOTES_COUNT
        volume = (MAX_DISTANCE - a["distance"]) / MAX_DISTANCE * MIDI_VOLUME_MAX
        print("Pitch %d, Volume %d" % (note, volume))

LED_COUNT = 60
def process_line(line, mylat, mylon):
    global next_slot
    global all_aircraft

    parts = line.split(",")
    if parts and (parts[0] == "MSG"):
        if parts[1] == "3":
            # Airborne position message
            try:
                aircraft_id = parts[4]
                altitude = int(parts[11])
                lat = float(parts[14])
                lon = float(parts[15])
                d = distance(lat, lon, mylat, mylon)
                b = bearing(mylat, mylon, lat, lon)
                if aircraft_id not in all_aircraft:
                    # New plane
                    slot = next_slot
                    next_slot = (next_slot + 1) % LED_COUNT
                    aircraft = {
                        "id": aircraft_id,
                        "altitude": altitude,
                        "lat": lat,
                        "lon": lon,
                        "distance": d,
                        "bearing": b,
                        "update": time.time(),
                        "slot": slot,
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
                for id, aircraft in all_aircraft.items():
                    #print_aircraft()
                    print_sound()
                # Purge things we haven't seen in 10 minutes
                for id, aircraft in all_aircraft.items():
                    if aircraft["update"] < time.time() - PURGE_TIME:
                        del all_aircraft[id]
                        print "Purged aircraft %s" % id
            except:
                pass
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
