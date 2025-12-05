print("main.py running...")
print("Initializing I2C buses...")

from machine import Pin, SoftI2C
from time import sleep, ticks_ms, ticks_diff
import urequests
import time

# ==========================================================
#  CONFIG: ThingSpeak API KEYS
# ==========================================================

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLQVJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"

TS_URL = "https://api.thingspeak.com/update"

# ==========================================================
#  SAFE SEND TO THINGSPEAK
# ==========================================================

def send_to_ts(api_key, fields):
    try:
        payload = "api_key=" + api_key
        for i, v in enumerate(fields, start=1):
            if v is None:
                v = 0
            payload += "&field{}={}".format(i, v)

        r = urequests.post(TS_URL, data=payload)
        r.close()
        print("→ TS:", api_key[:6], fields)
    except Exception as e:
        print("TS error:", e)

# ==========================================================
#  I2C BUS INITIALIZATION
# ==========================================================

i2c_A1 = SoftI2C(sda=Pin(19), scl=Pin(18), freq=100000)
i2c_A2 = SoftI2C(sda=Pin(23), scl=Pin(5),  freq=100000)

i2c_B1 = SoftI2C(sda=Pin(25), scl=Pin(26), freq=100000)
i2c_B2 = SoftI2C(sda=Pin(27), scl=Pin(14), freq=100000)

i2c_C1 = SoftI2C(sda=Pin(32), scl=Pin(0),  freq=80000)
i2c_C2 = SoftI2C(sda=Pin(15), scl=Pin(2),  freq=100000)

print("I2C ready.")

# ==========================================================
#  IMPORT SENSOR DRIVERS
# ==========================================================

from lib.sht30 import SHT30
from lib.hx711 import HX711
from lib.ltr390 import ltr_init_uv, ltr_read_uv
from lib.tsl2591 import TSL2591
from lib.vl53l0x_simple import vl_read

# ==========================================================
#  SENSOR OBJECTS
# ==========================================================

# ------ Model A ------
sht_air_A = SHT30(i2c_A2, addr=0x45)
sht_w2_A  = SHT30(i2c_A2, addr=0x44)
sht_amb_A = SHT30(i2c_A1, addr=0x45)

tsl_A = TSL2591(i2c_A2)
uv_A  = i2c_A1
dist_A = i2c_A1
hxA = HX711(34, 33)

# ------ Model B ------
sht_air_B = SHT30(i2c_B2, addr=0x45)
sht_w2_B  = SHT30(i2c_B2, addr=0x44)

tsl_B = TSL2591(i2c_B2)
uv_B  = i2c_B1
dist_B = i2c_B1
hxB = HX711(35, 33)

# ------ Model C ------
sht_air_C = SHT30(i2c_C2, addr=0x45)
sht_w2_C  = SHT30(i2c_C2, addr=0x44)

tsl_C = TSL2591(i2c_C2)
uv_C  = i2c_C1
dist_C = i2c_C1
hxC = HX711(36, 33)

# ------ Wind ------
wind_pin = Pin(13, Pin.IN)

# ==========================================================
#  SAFE READ FUNCTIONS (NEVER CRASH)
# ==========================================================

def safe_sht(s):
    try:
        return s.measure()
    except:
        return None, None

def safe_uv(i2c_bus):
    try:
        uvs, uvi = ltr_read_uv(i2c_bus)
        return uvs, uvi
    except:
        return None, None

def safe_tsl(t):
    try:
        return t.read_ir_lux()
    except:
        return None, None

def safe_dist(i2c_bus):
    try:
        d = vl_read(i2c_bus)
        return d
    except:
        return None

def safe_mass(hx):
    try:
        return hx.get_units(5)
    except:
        return None

def read_wind():
    try:
        return wind_pin.value()
    except:
        return 0

# ==========================================================
#  TABLE DISPLAY HELPER
# ==========================================================

def print_table(A, B, C, W):
    print("\n================ SENSOR DATA ================")
    print("[A]", A)
    print("[B]", B)
    print("[C]", C)
    print("[W] Wind =", W)
    print("=============================================\n")

# ==========================================================
#  MAIN LOOP (30 seconds)
# ==========================================================

print("\nStarting loop...\n")

while True:

    # -------- Model A --------
    TaA, RhA = safe_sht(sht_air_A)
    TwA, RwA = safe_sht(sht_w2_A)
    Tamb, Ramb = safe_sht(sht_amb_A)
    uvsA, uviA = safe_uv(uv_A)
    irA, luxA  = safe_tsl(tsl_A)
    dA = safe_dist(dist_A)
    mA = safe_mass(hxA)

    A_fields = [TaA, TwA, Tamb, uvsA, uviA, irA, luxA, dA, mA]

    # -------- Model B --------
    TaB, RhB = safe_sht(sht_air_B)
    TwB, RwB = safe_sht(sht_w2_B)
    uvsB, uviB = safe_uv(uv_B)
    irB, luxB  = safe_tsl(tsl_B)
    dB = safe_dist(dist_B)
    mB = safe_mass(hxB)

    B_fields = [TaB, TwB, uvsB, uviB, irB, luxB, dB, mB]

    # -------- Model C --------
    TaC, RhC = safe_sht(sht_air_C)
    TwC, RwC = safe_sht(sht_w2_C)
    uvsC, uviC = safe_uv(uv_C)
    irC, luxC  = safe_tsl(tsl_C)
    dC = safe_dist(dist_C)
    mC = safe_mass(hxC)

    C_fields = [TaC, TwC, uvsC, uviC, irC, luxC, dC, mC]

    # -------- Wind --------
    W_field = read_wind()

    # -------- Print Table --------
    print_table(A_fields, B_fields, C_fields, W_field)

    # -------- Send to ThingSpeak --------
    send_to_ts(API_A, A_fields)
    send_to_ts(API_B, B_fields)
    send_to_ts(API_C, C_fields)
    send_to_ts(API_W, [W_field])

    # -------- Wait 30 seconds --------
    sleep(30)


    print("Running main.py loop...")
    time.sleep(5)


