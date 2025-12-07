import time
import network
import urequests

from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.hx711 import HX711

from machine import I2C, Pin


# WiFi  
WIFI_SSID = "HUAWEI-1006VE_Wi-Fi5"
WIFI_PASS = "FPdGG9N7"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to WiFi…")
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Connected:", wlan.ifconfig())
    return wlan


# I2C Setup
i2c = I2C(0, scl=Pin(18), sda=Pin(19), freq=100000)


# Sensors – Model A
sht_A = SHT30(i2c, address=0x44)
ltr_A = LTR390(i2c)
tsl_A = TSL2591(i2c)
tof_A = VL53L0X(i2c)


# Sensors – Model B
sht_B = SHT30(i2c, address=0x45)
ltr_B = LTR390(i2c)
tsl_B = TSL2591(i2c)
tof_B = VL53L0X(i2c)


# Sensors – Model C
sht_C = SHT30(i2c, address=0x53)
ltr_C = LTR390(i2c)
tsl_C = TSL2591(i2c)
tof_C = VL53L0X(i2c)


# Wind Sensor (Anemometer) on GPIO13
wind_pin = Pin(13, Pin.IN, Pin.PULL_UP)
pulse_count = 0

def wind_interrupt(pin):
    global pulse_count
    pulse_count += 1

wind_pin.irq(trigger=Pin.IRQ_FALLING, handler=wind_interrupt)

def read_wind_speed():
    global pulse_count
    pulses = pulse_count
    pulse_count = 0

    # Standard conversion: 1 pulse = 2.4 km/h
    speed_kmh = pulses * 2.4
    return speed_kmh


# Sensor Reading Functions
def read_A():
    t, h = sht_A.measure()
    uv = ltr_A.read_uv()
    lux = tsl_A.read_lux()
    d = tof_A.read()
    return t, h, uv, lux, d

def read_B():
    t, h = sht_B.measure()
    uv = ltr_B.read_uv()
    lux = tsl_B.read_lux()
    d = tof_B.read()
    return t, h, uv, lux, d

def read_C():
    t, h = sht_C.measure()
    uv = ltr_C.read_uv()
    lux = tsl_C.read_lux()
    d = tof_C.read()
    return t, h, uv, lux, d

def read_wind():
    return read_wind_speed()


# ThingSpeak API Keys
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"

def send_ts(api_key, values):
    base = "https://api.thingspeak.com/update?api_key=" + api_key
    for i, v in enumerate(values, start=1):
        base += "&field{}={}".format(i, v)
    try:
        r = urequests.get(base)
        r.close()
        print("Uploaded →", api_key)
    except Exception as e:
        print("TS ERROR:", e)


# Main Program
connect_wifi()

print("\n>>> First reading (no send) <<<")
print("A:", read_A())
print("B:", read_B())
print("C:", read_C())
print("Wind:", read_wind())

print("\n=== STARTING LOOP (Every 30s) ===\n")

while True:
    time.sleep(30)

    A_vals = read_A()
    B_vals = read_B()
    C_vals = read_C()
    W_vals = (read_wind(),)

    send_ts(API_A, A_vals)
    send_ts(API_B, B_vals)
    send_ts(API_C, C_vals)
    send_ts(API_W, W_vals)

