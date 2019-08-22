#!/usr/bin/python

import datetime, os, signal, sys, time,json
from uptime import uptime

#LOGGING SETUP
import logging
logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %I:%M:%S %p',
                        filename='service.log'
                        )
logging.getLogger('apscheduler').setLevel(logging.WARNING)


#initiate start
logging.info('Gateway service restarted')
print('Gateway service restarted')


#CONFIGPARSER
CONFIGINI = 'config.ini'
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0
# instantiate
config = ConfigParser()
# parse existing file
config.read(CONFIGINI)

DEVICE_ID = config.get('attributes', 'device_id')
MAX_VALUE = int(config.get('setup', 'hum_max'))
MIN_VALUE = int(config.get('setup', 'hum_min'))
CAL_VALUE = int(config.get('setup', 'hum_cal'))

logging.info(MAX_VALUE)
print(MAX_VALUE)
logging.info(MIN_VALUE)
print(MIN_VALUE)
logging.info(CAL_VALUE)
print(CAL_VALUE)

#APSCHEDULER
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone="Asia/Kuala_Lumpur")

#MQTT SERVICE
import paho.mqtt.client as mqtt
#tele/airctrl0004/SENSOR
MQTT_TOPIC = "tele/"+DEVICE_ID+"/SENSOR"
MQTT_LWT = "tele/"+DEVICE_ID+"/LWT"
MQTT_COMMAND =  "cmnd/"+DEVICE_ID+"/SENSOR"
MQTT_STATE = "tele/"+DEVICE_ID+"/STATE"
MQTT_POWER = "stat/"+DEVICE_ID+"/POWER"
MQTT_RESULT = "stat/"+DEVICE_ID+"/RESULT"
mqtt_user = "lorafora"
mqtt_pass = "foralora"
mqttc = mqtt.Client()

#ADAFRUIT DHT
import Adafruit_DHT
DHT_sensor = Adafruit_DHT.DHT22

#GPIO
import RPi.GPIO as GPIO
DHT_pin = 17  # GPIO17 or other name GPIO0
SSR_pin = 16 #GPIO_EN_1   SSR
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(SSR_pin, GPIO.OUT)
#initiate off relay 0
GPIO.output(SSR_pin, 1)
relay_flag = 0



def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))
    print('MQTT service connected to broker')
    logging.info("rc: " + str(rc))
    logging.info('MQTT service connected to broker')

    ############################################################################

    mqttc.publish(MQTT_LWT, 'Online' ,qos=2,retain=True) #online status

    ############################################################################

    mqttc.subscribe(MQTT_COMMAND, qos=2)  # for callback to activate

def on_message(mqttc, obj, msg):
    #logging.debug(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    pass

def on_publish(mqttc, obj, mid):
    pass
    #logging.debug("mid: " + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    #pass
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, msg):
    #pass
    print(msg)
    logging.info(msg)


def on_handle_cmnd(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    logging.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    some_string = str(msg.payload.decode("utf-8", "ignore"))
    process_cmnd(some_string)


def publish_event(topics, pub_str):

    if pub_str != {}:
        try:
            mqttc.publish(topics, json.dumps(pub_str))
        except:
            print('Failed to publish to broker')
            logging.info('Failed to publish to broker')

def read_dht():

    global relay_flag

    now = datetime.datetime.now()
    format_iso_now = now.isoformat()

    try:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_sensor, DHT_pin)

        if humidity is not None and temperature is not None:

            print("real humidity: " +str(humidity))
            print(temperature,relay_flag)

            if 20 < humidity < 95  and 10 < temperature < 60:

                #calibration
                humidity = humidity + CAL_VALUE

                print("new humidity: " +str(humidity))

                print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
                logging.info("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))


                #round(a, 2)
                # {"Time":"2019-08-20T18:20:50", "AM2301":{"Temperature":22.5, "Humidity":54.6}, "TempUnit":"C"}
                data = {

                    "Time": format_iso_now,
                    "AM2301": {
                        "Temperature": round(temperature,2),
                        "Humidity": round(humidity,2)
                    },
                    "TempUnit": "C"
                }

                publish_event(MQTT_TOPIC,data)
                if humidity >= MAX_VALUE and relay_flag == 0:
                    on_relay()

                if humidity <= MIN_VALUE and relay_flag == 1:
                    off_relay()

                update_state()

            else:
                print("Failed to retrieve data from humidity sensor")
                logging.info("Failed to retrieve data from humidity sensor")

    except:
        print("Failed to retrieve data from humidity sensor")
        logging.info("Failed to retrieve data from humidity sensor")

def on_relay():
    global relay_flag

    GPIO.output(SSR_pin, 0)
    print('Relay1 activate')
    logging.info('Relay1 activate')
    relay_flag = 1

    data = {
        "POWER": "ON"
    }
    publish_event(MQTT_POWER,"ON")
    publish_event(MQTT_RESULT,data)


def off_relay():
    global relay_flag

    GPIO.output(SSR_pin, 1)
    print('Relay1 deactivate')
    logging.info('Relay1 deactivate')
    relay_flag = 0

    data = {
        "POWER": "OFF"
    }
    publish_event(MQTT_POWER,"OFF")
    publish_event(MQTT_RESULT,data)

def update_state():
    #{"Time": "2019-08-20T19:08:23", "Uptime": 1181, "Vcc": 3.208, "POWER": "ON",
    # "Wifi": {"AP": 1, "SSID": "loranet", "RSSI": 22, "APMac": "EC:08:6B:73:33:DC"}}
    now = datetime.datetime.now()
    format_iso_now = now.isoformat()

    data = {
        "Time": format_iso_now,
        "Uptime": uptime(),
        "Vcc": 3.208,
        "POWER": pin_status(),
    }

def pin_status():

    if relay_flag == 1:
        status = "ON"
    else:
        status = "OFF"
    return status

def process_cmnd(some_string):


    # Parse Data
    try:
        a, b, c = some_string.split('|')
    except ValueError:
        a = some_string
        b = ""
        c = ""
        try:
            a, b = some_string.split('|')
        except ValueError:
            a = some_string
            b = ""

    command = a
    code1 = b
    code2 = c

    logging.info('command: %s', command)
    logging.info('code1: %s', code1)
    logging.info('code2: %s', code2)
    print('command: %s', command)
    print('code1: %s', code1)
    print('code2: %s', code2)

    num = 0

    #########################################################wifi enable

    if command == 'HEARTBEAT':
        logging.info('HEARTBEAT request via MQTT')
        print('HEARTBEAT request via MQTT')
        update_state()

    #########################################################relay control
    #command for trigger relay send payload 'RELAY1|ON' or RELAY1|
    if command == 'RELAY':
        if code1 == 'ON':
            on_relay()
        if code1 == 'OFF':
            off_relay()
        if code1 == "TOGGLE":
            if relay_flag == 1:
                off_relay()
            if relay_flag == 0:
                on_relay()
        else:
            pass



#################################
    #command for reset python gateway.py OR restart pi
    if command == 'RESET':
        logging.info('Python RESET command received')
        logging.info('reset gateway.py')
        print('Python RESET command received')
        print('reset gateway.py')

        os.kill(os.getpid(), signal.SIGINT)

    ###################################################################

    if command == 'REBOOT':
        logging.info('OS REBOOT command received')
        print('OS REBOOT command received')
        os.system('reboot')

    ###################################################################


    if command == 'GW_UPDATE':
        logging.info('GW_UPDATE command received')
        os.system('/home/pi/numed/update.sh >/dev/null')

    else:
        pass


def mqtt_init():
    # mqttc.tls_set('/etc/ssl/certs/ca-certificates.crt')
    mqttc.will_set(MQTT_LWT, 'Offline', qos= 2, retain=True) #Put call to will_set before client.connect.
    mqttc.username_pw_set(mqtt_user, mqtt_pass)
    mqttc.connect("broker.loranet.my", 1883,60)   #client.connect

    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe
    # Uncomment to enable debug messages
    #mqttc.on_log = on_log

    #########################################################

    mqttc.message_callback_add(MQTT_COMMAND, on_handle_cmnd)

    #########################################################
    #mqttc.subscribe("$SYS/#", 0)

def cleanup(signum, frame):
    try:
        mqttc.publish(MQTT_LWT, 'Offline', qos= 2, retain=True)
        logging.info("Disconnecting from broker properly")
        print("Disconnecting from broker properly")
        mqttc.disconnect()
    except:
        logging.info("No broker?")
        print("No broker?")

    logging.info("RESTART. Exiting on signal " +str(signum))
    print("RESTART. Exiting on signal " + str(signum))
    sys.exit(signum)


def main():

    mqtt_init()
    #read hardware input
    scheduler.add_job(read_dht, 'interval', minutes=1) # every second
    #trigger_watchdog
    # scheduler.add_job(update_state, 'interval', minutes=5)  # every second
    scheduler.start()
    # start_watchdog()

    while True:
        mqttc.loop_start()
        time.sleep(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    main()


