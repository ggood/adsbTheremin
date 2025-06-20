#!/bin/sh

filename=`date +"%Y-%M-%d-%T.pkl"`

./recorder.py \
    --host 192.168.1.117 --port 30003 \
    --lat 37.3806017231717 --lon -122.08773836561024 \
    --output-file ${filename} $*
