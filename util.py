#!/usr/bin/env python3.9

"""
Some useful utilities for the ADSB theremin
"""

# TODO(ggood) consider adding a "power" argument, where the
# output alue is raised to the power (a float). But this 
# only works if normalized to 0.0-1.0.
# OR, scamp has this utility in scamp_extensions
def map_int(value, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return int((value - in_min) * (out_max - out_min) /
               (in_max - in_min) + out_min)

def constrain(value, min_value, max_value):
    """Constrain a value to be between min_value and max_value, inclusive."""
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

def map_bearing_to_pan(bearing):
    """
    Convert a plane's bearing to a MIDI pan controller value.
    """
    bearing = (int(bearing) + 270) % 360
    if bearing < 180:
        return map_int(bearing, 0, 180, 127, 0)
    return map_int(bearing, 180, 360, 0, 127)
