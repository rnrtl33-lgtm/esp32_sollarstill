import time
import network
import urequests
from machine import SoftI2C, Pin

# -----------------------------
# WIFI
# -----------------------------
SSID = "Abdullah's phone"
PASS = "42012999"

def wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(SSID, PASS)
        for _ in range(20):
            if sta.isconnected(): break
            time.sleep(1)
    print("WiFi:", sta.ifconfig())

wifi()

# -----------------------------
# API KEY MODEL B ONLY
# -----------------------------
API_B = "E8CTAK8MCUWLVQJ2"

# -----------------------------
# IMPORT LIBRARIES
# -----------------------------
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.vl53l0x import VL53L0X
from lib.tsl2591 import TSL2591

# -----------------------------
# SAFE FUNCTION
# -----------------------------
def safe(fn, fallback=0):
    try:
        return fn()
    except:
        return fallback

# -----------------------------
# I2C BUSES
# -----------------------------
# B1 bus
i2c_b1 = SoftI2C(scl=Pin(26), sda=Pin(25))

# B2 bus
i2c_b2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# -----------------------------
# INIT SENSORS WITH DELAYS
# -----------------------------
print("Initializing sensors...")

# ---- LTR390 ----
try:
    ltrB = LTR390(i2c_b1)
    time.sleep_ms(150)
except:
    ltrB = None
    print("LTR390_B FAIL")

# ---- VL53L0X ----
try:
    vl53B = VL53L0X(i2c_b1)
    time.sleep_ms(200)
except:
    vl53B = None
    print("VL53_B FAIL")

# ---- SHT30 sensors ----
try:
    shtAirB = SHT30(i2c_b2, addr=0x45)
except:
    shtAirB = None
    print("SHT Air FAIL")

try:
    shtW2B = SHT30(i2c_b2, addr=0x44)
except:
    shtW2B = None
    print("SHT Water FAIL")

# ---- TSL2591 ----
try:
    tslB = TSL2591(i2c_b2)
    time.sleep_ms(150)
except:
    tslB = None
    print("TSL FAIL")

print("MAIN STARTED — MODEL B ONLY")

# -----------------------------
# SEND TO THINGSPEAK
# -----------------------------
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

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:

    # ---- UV ----
    uv = 0
    if ltrB:
        uv = safe(lambda: ltrB.read_uv())

    # ---- Distance ----
    dist = 0
    if vl53B:
        dist = safe(lambda: vl53B.read())

    # ---- Air temp/humidity ----
    t_air = h_air = 0
    if shtAirB:
        t_air, h_air = safe(lambda: shtAirB.read(), (0,0))

    # ---- Water temp ----
    t_w2 = h_w2 = 0
    if shtW2B:
        t_w2, h_w2 = safe(lambda: shtW2B.read(), (0,0))

    # ---- Light ----
    lux = ir = 0
    if tslB:
        lux = safe(lambda: tslB.lux())
        ir  = safe(lambda: tslB.ir())

    # ---- SEND ----
    send_ts(API_B,
        field1 = uv,
        field2 = dist,
        field3 = t_air,
        field4 = t_w2,
        field5 = 0,
        field6 = lux,
        field7 = ir
    )

    print("B SENT — 15 seconds...\n")
    time.sleep(15)










   


