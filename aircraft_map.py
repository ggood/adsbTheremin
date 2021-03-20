import math
import time

DEFAULT_PURGE_TIME = 10  # Forget planes not heard from in this many seconds
EARTH_RADIUS = 6371000  # Earth's radius in meters


class Aircraft(object):
    def __init__(self, id):
        self._id = id
        self._altitude = 0
        self._latitude = 0.0
        self._longitude = 0.0
        self._update = 0.0

    @property
    def id(self):
        return self._id

    @property
    def altitude(self):
        return self._altitude

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    def __str__(self):
        return "%s: alt %d lat %f lon %f" % (
            self.id, self.altitude, self.latitude, self.longitude)

    def __repr__(self):
        return self.__str__()

    def update(self, altitude, latitude, longitude):
        self._altitude = altitude
        self._latitude = latitude
        self._longitude = longitude

    def distance_to(self, lat, lon):
        d_lat = math.radians(lat - self._latitude)
        d_lon = math.radians(lon - self._longitude)
        lat1_rad = math.radians(self._latitude)
        lat2_rad = math.radians(lat)

        a = (math.sin(d_lat/2) * math.sin(d_lat/2) +
            math.sin(d_lon/2) * math.sin(d_lon/2) *
            math.cos(lat1_rad) * math.cos(lat2_rad))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
        d = EARTH_RADIUS * c;
        return d

    def bearing_from(self, lat, lon):
        lat1_rad = math.radians(self._latitude)
        long1_rad = math.radians(self._longitude)
        lat2_rad = math.radians(lat)
        long2_rad = math.radians(lon)

        d_lon = long2_rad - long1_rad

        d_phi = math.log(
            math.tan(
                lat2_rad/2.0+math.pi/4.0)/math.tan(lat1_rad/2.0+math.pi/4.0))

        if abs(d_lon) > math.pi:
            if d_lon > 0.0:
                d_lon = -(2.0 * math.pi - dLong)
            else:
                d_lon = (2.0 * math.pi + dLong)

        bearing = (math.degrees(math.atan2(d_lon, d_phi)) + 360.0) % 360.0;
        return bearing


class AircraftMap(object):
    def __init__(self, latitude, longitude, purge_age=DEFAULT_PURGE_TIME):
        self._aircraft = {}  # ADSB ID -> aircraft
        self._latitude = latitude
        self._longitude = longitude

    def update(self, line):
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
                        aircraft = self._aircraft.get(aircraft_id)
                        if aircraft is None:
                            aircraft = Aircraft(aircraft_id)
                            self._aircraft[aircraft_id] = aircraft
                        aircraft.update(altitude, lat, lon)
                    except ValueError:
                        print("oops: %s" % line)
                        return
                except:
                    print("big oops: %s" % line)
                    raise


    def purge(self):
        for id, aircraft in all_aircraft.items():
            if aircraft._update < time.time() - PURGE_TIME:
                del self._aircraft[id]
                print("Purged aircraft %s" % id)

    def print_summary(self):
        print("%d aircraft" % len(self._aircraft))


    def closest(self, count):
        # I know there's a one-line list comprehension that will do
        # this, but I suck.
        dist_map = {}  # distance -> aircraft
        for id, aircraft in self._aircraft.items():
            dist = aircraft.distance_to(self._latitude, self._longitude)
            dist_map[dist] = aircraft
        closest = sorted(dist_map.keys())[:count]
        ret = [dist_map[d] for d in closest]
        return ret
