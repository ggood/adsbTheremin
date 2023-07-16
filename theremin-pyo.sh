#!/bin/sh

./theremin-pyo.py --host 192.168.1.117 --port 30003 \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --midi-channels 8 --polyphony 16 \
    --max-altitude 5000 --min-altitude 0 \
    --update-interval 0.1  --shift 2 
