# ==================================================
# main.py — Stable System A+B+C+D
# ThingSpeak SAFE RATE (NO -202)
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

# ------------------
# Libraries
# ------------------
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.hx711_clean import HX711

# ------------------
# ThingSpeak API KEYS
# ------------------
API_A = "PUT_API_KEY_A"
API_B = "PUT_API_KEY_B"
API_C = "PUT_API_KEY_C"
API_D = "PUT_API_KEY_D"

# ------------------
# I2C BUSES
# ------------------
# Model A
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
# Model B
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
# Model C
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
# Model D
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ------------------
# Sensors Init
# ------------------
# A
A_air = SHT30(i2cA, 0x45)
A_wat = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)
hxA = HX711(34, 33)

# B
B_air = SHT30(i2cB, 0x45)
B_wat = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

# C
C_air = SHT30(i2cC, 0x45)
C_wat = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

# D
D_uv = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# Wind
wind_pulses = 0
wind_pin = Pin(13, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ------------------
# ThingSpeak Sender
# ------------------
def send_ts(api, data):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ------------------
# MAIN LOOP
# ------------------
print("\n=== SYSTEM RUNNING (STABLE) ===\n")

cycle = 0

while True:

    # ===== MODEL A =====
    Ta, _ = A_air.measure()
    Tw, _ = A_wat.measure()
    try:
        Da = A_dist.read()
    except:
        Da = 0
    Wa = hxA.get_weight()

    dataA = {
        "T_air": Ta,
        "T_wat": Tw,
        "Dist": Da,
        "Weight": Wa
    }

    # ===== MODEL B =====
    Tb, _ = B_air.measure()
    Twb, _ = B_wat.measure()
    try:
        Db = B_dist.read()
    except:
        Db = 0

    dataB = {
        "T_air": Tb,
        "T_wat": Twb,
        "Dist": Db
    }

    # ===== MODEL C =====
    Tc, _ = C_air.measure()
    Twc, _ = C_wat.measure()
    try:
        Dc = C_dist.read()
    except:
        Dc = 0

    dataC = {
        "T_air": Tc,
        "T_wat": Twc,
        "Dist": Dc
    }

    # ===== MODEL D =====
    UV = D_uv.read_uv()
    full, IR = D_lux.get_raw_luminosity()
    LUX = D_lux.calculate_lux(full, IR)

    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4

    dataD = {
        "UV": UV,
        "IR": IR,
        "LUX": LUX,
        "WIND": WIND
    }

    # ----- PRINT -----
    print("-" * 60)
    print("A | T_air:", round(Ta,2), "T_wat:", round(Tw,2), "Dist:", Da, "Weight:", round(Wa,1))
    print("B | T_air:", round(Tb,2), "T_wat:", round(Twb,2), "Dist:", Db)
    print("C | T_air:", round(Tc,2), "T_wat:", round(Twc,2), "Dist:", Dc)
    print("D | UV:", UV, "IR:", IR, "LUX:", round(LUX,1), "WIND:", WIND)

    # ----- SEND WITH SAFE DELAY -----
    send_ts(API_A, dataA)
    time.sleep(16)

    send_ts(API_B, dataB)
    time.sleep(16)

    send_ts(API_C, dataC)
    time.sleep(16)

    send_ts(API_D, dataD)
    time.sleep(16)

    cycle += 1
    if cycle >= 15:
        print("Auto reset for OTA...")
        time.sleep(2)
        reset()

    gc.collect()
