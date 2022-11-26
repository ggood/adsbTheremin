#!/bin/sh

./file_player.py \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --midi-channels 8 \
    --max_altitude 20000 --min_altitude 500 \
    --time_factor 10 \
    --file $1
