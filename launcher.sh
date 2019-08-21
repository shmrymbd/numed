#!/bin/sh
cd /home/pi/numed
if pgrep -f 'python3 gateway.py' >/dev/null ;then
    echo "gateway.py already running"
else python3 gateway.py  >/dev/null 2>&1 &
    echo "starting gateway.py....."
fi


