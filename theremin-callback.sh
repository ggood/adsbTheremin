#!/bin/sh

./theremin-callback.py --host 192.168.1.117 --port 30003 \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --midi-channels 8 --polyphony 8 \
    --max-altitude 5000 --min-altitude 0 \
    --shift 7
