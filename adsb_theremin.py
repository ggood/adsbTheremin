#!/usr/bin/env python

import argparse
import math
import socket
import sys

EARTH_RADIUS = 6371000

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

def process_line(line, mylat, mylon):
    parts = line.split(",")
    if parts and parts[0] == "MSG":
        if parts[1] == "3":
            # Airborne position message
            try:
                aircraft_id = parts[4]
                altitude = int(parts[11])
                lat = float(parts[14])
                lon = float(parts[15])
                print (
                    "mode-s id %s alt %5d lat %6.2f lon %6.2f dist %5.0f m "
                    "bearing %0.0f deg" %
                    (aircraft_id, altitude, lat, lon,
                     distance(lat, lon, mylat, mylon),
                     bearing(mylat, mylon, lat, lon)))
            except:
                sys.stderr.write("Ignored %s" % line)
                raise

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
                        help="IP address or hostname of host running dump1090")
    parser.add_argument("-p", "--port", type=int,
                        help="Port for dump1090 server")
    parser.add_argument("--lat", type=float, help="Your latitude")
    parser.add_argument("--lon", type=float, help="Your longitude")

    args = parser.parse_args()

    theremin(args.host, args.port, args.lat, args.lon)


if __name__ == "__main__":
    main()
