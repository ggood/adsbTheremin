#!/bin/sh

./theremin-pyo-file.py  \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --polyphony 2 \
    --max_altitude 5000 --min_altitude 0 \
    --input_file /tmp/adsb.dat --playback_factor 20
