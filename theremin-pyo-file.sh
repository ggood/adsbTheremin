#!/bin/sh

./theremin-pyo-file.py  \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --polyphony 4 \
    --max-altitude 40000 --min-altitude 200 \
    --playback-factor 1 \
    $*
