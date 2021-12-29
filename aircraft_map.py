# aircraft_map: maintains a list of aircraft "seen" by an ADSB
# receiver.

import copy
import math
import time

DEFAULT_PURGE_TIME = 120  # Forget planes not heard from in this many seconds
DEFAULT_PURGE_INTERVAL = 1  # How often to purge stale aircraft
EARTH_RADIUS = 6371000  # Earth's radius in meters


class Aircraft(object):
    """Represents a single aircraft"""
    def __init__(self, id):
        self._id = id
        self._altitude = 0
        self._latitude = 0.0
        self._longitude = 0.0
        self._update = 0.0
        self._create_time = time.time()

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
        """Update an aircraft's altitude, latitude, and longitude"""
        self._altitude = altitude
        self._latitude = latitude
        self._longitude = longitude
        self._update = time.time()
        print("%s update time %f age %f" % (self._id, self._update, time.time() - self._create_time))

    def distance_to(self, lat, lon):
        """
        Compute the distance from the aircraft to the point given by
        lat and lon. This does not consider the aircraft's altitude. In
        other words, this computes the distance to the projection
        of the aircraft on the ground.
        """
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
        """
        Compute the bearing, in degrees, of the aircraft as seen from
        the position given by lat and lon.
        """
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
    """
    This class keeps track of aircraft heard by an ADSB receiver.
    You can feed all lines returned by the ADSB receiver into this
    code, and it will consume all airborne position messages and update
    the list of aircraft.
    Aircraft not heard from in purge_age seconds will be discarded.
    """
    def __init__(self, latitude, longitude, purge_age=DEFAULT_PURGE_TIME):
        """
        Arguments:
        latitude: the latitude, in fractional degrees, of the observer.
        longitude: the longitude, in fractional degrees, of the observer.
        purge_age: the time, in seconds, after which aircraft will be
                   discarded if no position updates have been seen.
        """
        self._aircraft = {}  # ADSB ID -> aircraft
        self._latitude = latitude
        self._longitude = longitude
        self._purge_age = purge_age
        self._start_time = self._last_purge = time.time()

    def update(self, line):
        self._purge()
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
                            print("Added %s at time %f" % (aircraft_id, time.time() - self._start_time))
                        aircraft.update(altitude, lat, lon)
                    except ValueError:
                        # Some position messages omit the lat/lon. Ignore.
                        return
                except:
                    print("big oops: %s" % line)
                    raise

    def _purge(self):
        if time.time() - self._last_purge < DEFAULT_PURGE_INTERVAL:
            return
        print("purge at %f" % (time.time() - self._start_time))
        n = 0
        prev_aircraft = copy.deepcopy(self._aircraft)
        for id, aircraft in list(self._aircraft.items()):
            if aircraft._update < time.time() - self._purge_age:
                print("Deleting %s, update %f at time %f" % (id, aircraft._update, time.time() - self._start_time))
                del self._aircraft[id]
                n += 1
        print("purged %d aircraft, %d remaining" % (n, len(self._aircraft)))
        if len(self._aircraft) == 0:
            import pdb; pdb.set_trace()
        self._last_purge = time.time()

    def print_summary(self):
        print("%d aircraft" % len(self._aircraft))

    def closest(self, count, min_altitude=0, max_altitude=100000):
        """
        Return the closest [count] aircraft. If min_altitude or
        max_altitude is provided, limit the retured results to
        aircraft in that range. May return fewer than <count>
        aircraft.
        """
        # I know there's a one-line list comprehension that will do
        # this, but I suck.
        ret = []
        dist_map = {}  # distance -> aircraft
        for id, aircraft in self._aircraft.items():
            dist = aircraft.distance_to(self._latitude, self._longitude)
            dist_map[dist] = aircraft
        closest = sorted(dist_map.keys())
        for d in closest:
            aircraft = dist_map[d]
            if (aircraft.altitude <= max_altitude and
                   aircraft.altitude >= min_altitude):
                ret.append(aircraft)
            if len(ret) >= count:
                return ret
        return ret


    def count(self):
        """
        Return the count of aircraft in the map.
        """
        return len(self._aircraft)
