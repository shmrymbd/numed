#!/bin/sh

cd /home/pi/numed
mv launcher.sh launcher.sh.bak

git fetch --all
git reset --hard origin/master
#git pull
#comment during testing
pip3 install -r requirements.txt
sleep 2
pkill -f 'python3 gateway.py'


cd /home/pi/
chown -R dyna:dyna gateway_boardV2/

sleep 2
cd /home/pi/numed/
python3 gateway.py >/dev/null 2>&1 &
    echo "starting gateway.py....."

