#!/bin/sh

./theremin.py --host 192.168.1.117 --port 30003 \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --midi-channels 8 --polyphony 8 \
    --max_altitude 20000 --min_altitude 1000 \
    --update_interval 30  --shift 7 