#!/usr/bin/env python

# Older version of code - keeping in git repo because this has
# code to drive a strip of Neopixels. Someday I'll re-incorporate
# this into the code.

import argparse
import colorsys
import math
import socket
import sys
import time

EARTH_RADIUS = 6371000

# LED strip imports and params
from neopixel import *

LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 5
LED_BRIGHTNESS = 255
LED_INVERT = False

WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)

PURGE_TIME = 10

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                          LED_INVERT, LED_BRIGHTNESS)
# Create a spectrum of 255 values ranging from blue to red
HSV_tuples = [((x*0.7+0.3)/256, 1.0, 1.0) for x in range(256)]
RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
RGB_ntuples = []
for r, g, b in RGB_tuples:
    RGB_ntuples.append(Color(int(r * 255), int(g * 255), int(b * 255)))

# End LED strip config

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
    return RGB_ntuples[255 - scaled_distance]


def update_leds():
    ids = all_aircraft.keys()[0:LED_COUNT]  # Just in case we're receiving a lot

    for id in ids:
        aircraft = all_aircraft[id]
        led = aircraft["slot"]  # TODO: invert LED order
        strip.setPixelColor(led, get_color(aircraft))
    strip.show()


def pulse_led(led):
    old_color = strip.getPixelColor(led)
    strip.setPixelColor(led, BLACK)
    strip.show()
    time.sleep(0.03)
    strip.setPixelColor(led, old_color)
    strip.show()

def print_aircraft():
    print("")
    for a in sorted(all_aircraft.values(), key=lambda x: x["slot"]):
        print("%d: id %s alt %5d lat %6.2f lon %6.2f dist %5.0f m "
               "bearing %0.0f deg" %
               (a["slot"], a["id"], a["altitude"], a["lat"], a["lon"],
                a["distance"], a["bearing"]))

def process_line(line, mylat, mylon):
    global next_slot
    global all_aircraft

    parts = line.split(",")
    if parts and parts[0] == "MSG":
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
                    pulse_led(aircraft["slot"])
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
                    print_aircraft()
                # Purge things we haven't seen in 10 minutes
                for id, aircraft in all_aircraft.items():
                    if aircraft["update"] < time.time() - PURGE_TIME:
                        del all_aircraft[id]
                        print("Purged aircraft %s" % id)
                        strip.setPixelColor(aircraft["slot"], BLACK)
                        strip.show()
                update_leds()
            except:
                sys.stderr.write("Ignored %s" % line)
                raise

def theremin(host, port, mylat, mylon):
    print("Connect to %s:%d" % (host, port))

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
                        help="IP address or hostname of host running dump1090")
    parser.add_argument("-p", "--port", type=int,
                        help="Port for dump1090 server")
    parser.add_argument("--lat", type=float, help="Your latitude")
    parser.add_argument("--lon", type=float, help="Your longitude")

    args = parser.parse_args()

    # Set up LED strip and turn all LEDs off
    strip.begin()
    for i in range(LED_COUNT):
        strip.setPixelColor(i, BLACK)
    strip.show()

    theremin(args.host, args.port, args.lat, args.lon)


if __name__ == "__main__":
    main()
