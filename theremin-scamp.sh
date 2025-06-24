#!/bin/sh

ADSB_HOST="${ADSB_HOST:-127.0.0.1}"

./theremin-scamp.py --host ${ADSB_HOST} --port 30003 \
    --lat 37.420975 --lon -122.172351 \
    --midi-channels 8 --polyphony 8 \
    --max-altitude 10000 --min-altitude 0 \
    --max-distance 50000

#    --lat 37.322649 --lon -121.963315 \  # Barnes/Noble Santa Clara
#    --lat 37.420975 --lon -122.172351 \  # CCRMA
