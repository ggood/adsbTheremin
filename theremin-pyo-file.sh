#!/bin/sh

./theremin-pyo-file.py  \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --polyphony 20 \
    --max_altitude 40000 --min_altitude 200 \
    --input_file data/adsb.dat --playback_factor 10
