import time
import network
import urequests
from machine import I2C, SoftI2C, Pin

# ===================================
# WIFI
# ===================================
SSID = "Abdullah's phone"
PASS = "42012999"

def wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(SSID, PASS)
        t = 20
        while not sta.isconnected() and t > 0:
            print("Connecting WiFi...")
            time.sleep(1)
            t -= 1
    print("WiFi:", sta.ifconfig())

wifi()

# ===================================
# ThingSpeak API (MODEL B)
# ===================================
API_B = "E8CTAK8MCUWLVQJ2"

# ===================================
# IMPORT SENSOR LIBRARIES
# ===================================
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.vl53l0x import VL53L0X
from lib.tsl2591 import TSL2591

# ===================================
# SAFE READ WRAPPER
# ===================================
def safe(fn, fallback=0):
    try:
        return fn()
    except:
        return fallback

# ===================================
# I2C BUS DEFINITIONS — MODEL B
# ===================================
# B1: LTR390_B + VL53L0X_B
i2c_b1 = SoftI2C(scl=Pin(26), sda=Pin(25))

# B2: SHT30-Air_B + SHT30-W2_B + TSL2591_B
i2c_b2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# ===================================
# SENSOR INITIALIZATION — MODEL B
# ===================================
ltrB   = LTR390(i2c_b1)
vl53B  = VL53L0X(i2c_b1)
shtAirB = SHT30(i2c_b2, addr=0x45)
shtW2B  = SHT30(i2c_b2, addr=0x44)
tslB    = TSL2591(i2c_b2)

# ===================================
# SEND TO THINGSPEAK
# ===================================
def send_ts(api, **fields):
    url = "https://api.thingspeak.com/update?api_key=" + api
    for k, v in fields.items():
        url += f"&{k}={v}"
    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except:
        print("TS ERROR")

# ===================================
# MAIN LOOP — MODEL B ONLY
# ===================================
print("MAIN STARTED — MODEL B ONLY")

while True:

    # UV
    uv = safe(lambda: ltrB.read_uv())

    # Distance
    dist = safe(lambda: vl53B.read())

    # Temperature / humidity (Air)
    t_air, h_air = safe(lambda: shtAirB.read(), (0,0))

    # Water temperature
    t_w2, h_w2 = safe(lambda: shtW2B.read(), (0,0))

    # Light (Lux + IR)
    lux = safe(lambda: tslB.lux())
    ir  = safe(lambda: tslB.ir())

    # SEND
    send_ts(API_B,
        field1 = uv,
        field2 = dist,
        field3 = t_air,
        field4 = t_w2,
        field5 = 0,      # مكان HX711 (محذوف)
        field6 = lux,
        field7 = ir
    )

    print("B SENT. Sleeping 15 sec...\n")
    time.sleep(15)










   


