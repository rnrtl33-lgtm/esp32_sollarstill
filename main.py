# ==================================================
# main.py — FINAL STABLE SYSTEM (A+B+C+D)
# Temp + Distance + Weight + UV + Lux + Wind
# ThingSpeak + OTA Reset-cycle
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.hx711_clean import HX711
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591

# ---------------- ThingSpeak Keys ----------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# ---------------- I2C ----------------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ---------------- Sensors ----------------
A_air = SHT30(i2cA, 0x45)
A_wat = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)

hxA = HX711(34, 33)
hxA.offset = -89279.512
hxA.scale  = 395.6556

B_air = SHT30(i2cB, 0x45)
B_wat = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

C_air = SHT30(i2cC, 0x45)
C_wat = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

uvD  = LTR390(i2cD)
luxD = TSL2591(i2cD)

# ---------------- Wind ----------------
wind_pulses = 0
def wind_cb(pin):
    global wind_pulses
    wind_pulses += 1

Pin(13, Pin.IN).irq(trigger=Pin.IRQ_RISING, handler=wind_cb)

# ---------------- ThingSpeak ----------------
def send_ts(api, fields):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=" + api
        for i, v in enumerate(fields, 1):
            url += "&field{}={}".format(i, v)
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ---------------- MAIN LOOP ----------------
print("\n=== SYSTEM RUNNING (STABLE) ===\n")
cycle = 0

while True:
    TaA,_ = A_air.measure()
    TwA,_ = A_wat.measure()
    DaA = A_dist.read()
    Wa  = hxA.get_weight()

    TaB,_ = B_air.measure()
    TwB,_ = B_wat.measure()
    Db  = B_dist.read()

    TaC,_ = C_air.measure()
    TwC,_ = C_wat.measure()
    Dc  = C_dist.read()

    UV  = uvD.read_uv()
    full, ir = luxD.get_raw_luminosity()
    LUX = luxD.calculate_lux(full, ir)

    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4

    print("-"*60)
    print("A | T_air:",TaA,"T_wat:",TwA,"Dist:",DaA,"Weight:",round(Wa,1))
    print("B | T_air:",TaB,"T_wat:",TwB,"Dist:",Db)
    print("C | T_air:",TaC,"T_wat:",TwC,"Dist:",Dc)
    print("D | UV:",UV,"LUX:",round(LUX,1),"WIND:",WIND)

    send_ts(API_A, [TaA, TwA, DaA, Wa])
    send_ts(API_B, [TaB, TwB, Db])
    send_ts(API_C, [TaC, TwC, Dc])
    send_ts(API_D, [WIND, UV, LUX, ir])

    cycle += 1
    if cycle >= 15:
        print("Auto reset for OTA...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
