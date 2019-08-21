#!/bin/sh

cd /home/pi/numed
mv launcher.sh launcher.sh.bak
pkill -f 'python3 gateway.py'

git fetch --all
git reset --hard origin/master

#comment during testing
pip3 install -r requirements.txt
sleep 1
pkill -f 'python3 gateway.py'


cd /home/pi/
chown -R pi:pi numed/

sleep 1
cd /home/pi/numed/
python3 gateway.py >/dev/null 2>&1 &
    echo "starting gateway.py....."

