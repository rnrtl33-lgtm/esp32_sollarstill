# ==============================
# main.py — MODEL B ONLY (OTA Update)
# ==============================

import time, gc
from machine import Pin, SoftI2C, reset

# ---- Libraries ----
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X
from lib.hx711_simple import HX711

# ==============================
# ThingSpeak API (MODEL B)
# ==============================
API_B = "E8CTAK8MCUWLVQJ2"

# ==============================
# I2C (MODEL B)
# ==============================
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# ==============================
# HX711 (MODEL B)
# ==============================
hxB = HX711(35, 33)

# ==============================
# Sensors (MODEL B)
# ==============================
B_air   = SHT30(i2c_B2, 0x45)
B_wat   = SHT30(i2c_B2, 0x44)
B_uv    = LTR390(i2c_B1)
B_lux   = TSL2591(i2c_B2)
B_laser = VL53L0X(i2c_B1)

# ==============================
# ThingSpeak Sender
# ==============================
def send_ts(api, data):
    try:
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        import urequests
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ==============================
# MAIN LOOP
# ==============================
print("\n>>> OTA UPDATE: MODEL B ONLY <<<\n")

START = time.time()

while True:
    # ---- READ MODEL B ----
    T_air, H_air = B_air.measure()
    T_wat, H_wat = B_wat.measure()

    ALS = B_uv.read_als()
    UV  = B_uv.read_uv()

    full, IR = B_lux.get_raw_luminosity()
    LUX = B_lux.calculate_lux(full, IR)

    try:
        DIST = B_laser.read()
    except:
        DIST = None

    WEIGHT = hxB.get_weight()

    dataB = {
        "T_air": T_air,
        "H_air": H_air,
        "T_wat": T_wat,
        "H_wat": H_wat,
        "ALS": ALS,
        "UV": UV,
        "LUX": LUX,
        "IR": IR,
        "DIST_mm": DIST,
        "WEIGHT_g": WEIGHT
    }

    print("MODEL B:", dataB)

    send_ts(API_B, dataB)

    time.sleep(20)

    # ---- OTA LIVE RESET (≈5 minutes) ----
    if time.time() - START > 300:
        print("OTA cycle restart...")
        time.sleep(2)
        reset()

    gc.collect()
