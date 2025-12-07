import time
import network
import urequests
from machine import Pin, I2C
from lib.sht30 import SHT30
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.ltr390 import LTR390


# -----------------------------
#   WIFI
# -----------------------------
SSID = "Abdullah"
PW   = "42012999"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PW)
        while not wlan.isconnected():
            time.sleep(0.3)
    print("WiFi:", wlan.ifconfig())


# -----------------------------
#   THINGSPEAK KEYS
# -----------------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

CHANNEL = {
    'A': API_A,
    'B': API_B,
    'C': API_C,
    'D': API_D
}


# -----------------------------
#   I2C
# -----------------------------
i2c = I2C(0, scl=Pin(18), sda=Pin(19))


# -----------------------------
#   SAFE SENSOR READERS
# -----------------------------
def read_sht30():
    try:
        s = SHT30(i2c)
        t, h = s.measure()
        return t, h
    except:
        return 0, 0


def read_ltr390():
    try:
        s = LTR390(i2c)
        return s.uvi()
    except:
        return 0


def read_tsl2591():
    try:
        s = TSL2591(i2c)
        lux = s.get_lux()
        ir = s.get_ir()
        return lux, ir
    except:
        return 0, 0


def read_vl53():
    try:
        s = VL53L0X(i2c)
        d = s.read()
        return d
    except:
        return 0


# -----------------------------
#   MODEL DETECTION
# -----------------------------
def detect_model():
    scan = [hex(x) for x in i2c.scan()]
    # VL53 (0x29), SHT30 (0x44/0x45), TSL (0x29 if same bus), LTR (0x53)
    # نستخدم نفس المنطق القديم
    if '0x53' in scan and '0x29' in scan and '0x44' in scan:
        return 'A'
    if '0x29' in scan and '0x44' in scan:
        return 'B'
    if '0x29' in scan and '0x45' in scan:
        return 'C'
    return 'D'


# -----------------------------
#   SEND TO THINGSPEAK
# -----------------------------
def send(model, fields):
    api = CHANNEL[model]
    url = "https://api.thingspeak.com/update?api_key=" + api

    for i, v in enumerate(fields, start=1):
        url += f"&field{i}={v}"

    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except:
        print("TS ERROR")


# -----------------------------
#   MAIN LOOP
# -----------------------------
wifi_connect()
model = detect_model()
print("Detected Model:", model)

print("MAIN STARTED")

while True:

    # -----------------------------
    # MODEL A
    # -----------------------------
    if model == 'A':
        t1, h1 = read_sht30()          # Field 1
        uv    = read_ltr390()          # Field 2
        dis   = read_vl53()            # Field 3
        t2, h2 = read_sht30()          # Field 4 & 5 (Air + W2)
        lux, ir = read_tsl2591()       # Field 6 & 7

        fields = [t1, uv, dis, t2, h2, lux, ir]
        send('A', fields)
        print("A SENT →", fields)
        time.sleep(15)

    # -----------------------------
    # MODEL B
    # -----------------------------
    elif model == 'B':
        uv    = read_ltr390()
        dis   = read_vl53()
        t, h  = read_sht30()
        t2, h2 = read_sht30()
        lux, ir = read_tsl2591()

        fields = [uv, dis, t, h, t2, h2, lux, ir]
        send('B', fields)
        print("B SENT →", fields)
        time.sleep(15)

    # -----------------------------
    # MODEL C
    # -----------------------------
    elif model == 'C':
        uv    = read_ltr390()
        dis   = read_vl53()
        t, h  = read_sht30()
        t2, h2 = read_sht30()
        lux, ir = read_tsl2591()

        fields = [uv, dis, t, h, t2, h2, lux]
        send('C', fields)
        print("C SENT →", fields)
        time.sleep(15)

    # -----------------------------
    # MODEL D (WIND)
    # -----------------------------
    elif model == 'D':
        wind_pin = Pin(13, Pin.IN)
        wind_speed = wind_pin.value()

        fields = [wind_speed]
        send('D', fields)
        print("D SENT →", fields)
        time.sleep(15)











   


