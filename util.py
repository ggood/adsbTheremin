#!/usr/bin/env python3.9

def map_int(value, in_min, in_max, out_min, out_max):
    """
    Map input from one range to another.
    """
    return int((value - in_min) * (out_max - out_min) /
               (in_max - in_min) + out_min)

def constrain(value, min, max):
    if value < min:
        return min
    if value > max:
        return max
    return value

def map_bearing_to_pan(bearing):
    """
    Convert a plane's bearing to a MIDI pan controller value.
    """
    bearing = (int(bearing) + 270) % 360
    if bearing < 180:
        return map_int(bearing, 0, 180, 127, 0)
    return map_int(bearing, 180, 360, 0, 127)

