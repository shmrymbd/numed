#!/bin/sh

cd /home/dyna/gateway_boardV2
cp config_file.ini /home/dyna
cp ./web/config/db.sqlite3 /home/dyna
mv launcher.sh launcher.sh.bak

sleep 5
#pkill -f 'python3 gateway.py'
pkill -f 'python3 manage.py runserver 0.0.0.0:80'
pkill -f 'python3 watchdog.py'

apt-get install memcached
git fetch --all
git reset --hard origin/master
#git pull
#comment during testing
pip3 install -r requirements.txt
sleep 2
pkill -f 'python3 gateway.py'
pkill -f 'python3 manage.py runserver 0.0.0.0:80'
pkill -f 'python3 watchdog.py'

cd /home/dyna/
cp config_file.ini ./gateway_boardV2/
cp db.sqlite3 ./gateway_boardV2/web/config/
chown -R dyna:dyna gateway_boardV2/

sleep 2
cd /home/dyna/gateway_boardV2/
python3 gateway.py >/dev/null 2>&1 &
    echo "starting gateway.py....."
sleep 2
cd /home/dyna/gateway_boardV2/web/config
python3 manage.py runserver 0.0.0.0:80 >/dev/null 2>&1 &
    echo "starting web....."
