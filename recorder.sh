#!/bin/sh

./recorder.py \
    --host 192.168.1.117 --port 30003 \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --output-file /tmp/adsb.dat $*
