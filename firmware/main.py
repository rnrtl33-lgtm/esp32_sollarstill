import time
import network
import urequests

from lib.sht30 import SHT30
#from lib.ltr390 import LTR390   # تم إلغاؤه نهائيًا
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.hx711 import HX711

from machine import I2C, Pin


# -----------------------------
# WiFi
# -----------------------------
WIFI_SSID = "HUAWEI-1006VE_Wi-Fi5"
WIFI_PASS = "FPdGG9N7"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Connected:", wlan.ifconfig())
    return wlan


# -----------------------------
# ThingSpeak API KEYS
# -----------------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"


# -----------------------------
# Sensors Init (I2C)
# -----------------------------
i2c = I2C(0, scl=Pin(18), sda=Pin(19))

# حذف حساس LTR390 كاملًا
# time.sleep_ms(1200)  # لم يعد ضروريًا

sht = SHT30(i2c)
tsl = TSL2591(i2c)
tof = VL53L0X(i2c)

hx = HX711(d_out=12, pd_sck=14)
hx.tare()

# حساس الرياح على GPIO13
wind_pin = Pin(13, Pin.IN)


# -----------------------------
# Send to ThingSpeak
# -----------------------------
def send_ts(api_key, vals):
    try:
        url = (
            "https://api.thingspeak.com/update?api_key={}&field1={}&field2={}&field3={}"
        ).format(api_key, vals[0], vals[1], vals[2])
        r = urequests.get(url)
        r.close()
        print("Uploaded ->", api_key)
    except Exception as e:
        print("TS ERROR:", e)


# -----------------------------
# Read Functions
# -----------------------------
def read_A():
    t, h = sht.measure()
    lux = tsl.lux()
    dist = tof.read()
    return (t, h, lux)

def read_B():
    return read_A()

def read_C():
    t, h = sht.measure()
    dist = tof.read()
    return (t, h, dist)

def read_W():
    return (wind_pin.value(), 0, 0)


# -----------------------------
# Main Loop
# -----------------------------
print("\nStarting first readings...")
print("A:", read_A())
print("B:", read_B())
print("C:", read_C())
print("W:", read_W())

print("\n== ENTERING LOOP ==")

while True:
    time.sleep(30)

    A_vals = read_A()
    B_vals = read_B()
    C_vals = read_C()
    W_vals = read_W()

    send_ts(API_A, A_vals)
    send_ts(API_B, B_vals)
    send_ts(API_C, C_vals)
    send_ts(API_W, W_vals)

