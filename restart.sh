#!/bin/sh
pkill -f 'python3 gateway.py'

sleep 1
cd /home/pi/numed
python3 gateway.py  >/dev/null 2>&1 &
    echo "starting gateway.py....."
