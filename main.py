# =====================================================
# main.py — FINAL STABLE SYSTEM (A+B+C+D)
# Weight only on Model A
# ThingSpeak + OTA reset-cycle
# =====================================================

import time, gc
from machine import Pin, SoftI2C, reset

# -----------------------
# Libraries
# -----------------------
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.tsl2591_fixed import TSL2591
from lib.ltr390_clean import LTR390
from lib.hx711_clean import HX711

# -----------------------
# ThingSpeak API KEYS
# -----------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

SEND_INTERVAL = 20      # ThingSpeak limit
AUTO_RESET_SEC = 300    # 5 minutes

# -----------------------
# I2C BUSES
# -----------------------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# -----------------------
# MODEL A
# -----------------------
A_air = SHT30(i2cA, 0x45)
A_wat = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)

hx = HX711(dt=34, sck=33)
hx.offset = -89279.512   # من معايرتك
hx.scale  = 395.6556

# -----------------------
# MODEL B
# -----------------------
B_air = SHT30(i2cB, 0x45)
B_wat = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

# -----------------------
# MODEL C
# -----------------------
C_air = SHT30(i2cC, 0x45)
C_wat = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

# -----------------------
# MODEL D
# -----------------------
uv_d = LTR390(i2cD)
tsl_d = TSL2591(i2cD)

wind_pulses = 0
wind_pin = Pin(13, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# -----------------------
# ThingSpeak sender
# -----------------------
def send_ts(api, data):
    try:
        url = "https://api.thingspeak.com/update?api_key=" + api
        for field, value in data.items():
            url += "&field{}={}".format(field, value)
        import urequests
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# -----------------------
# MAIN LOOP
# -----------------------
print("\n=== SYSTEM RUNNING (STABLE) ===\n")
start_time = time.time()

while True:
    # -------- A --------
    Ta, _ = A_air.measure()
    Tw, _ = A_wat.measure()
    try:
        Da = A_dist.read()
    except:
        Da = 0

    Wa = hx.get_weight()
    if abs(Wa) < 2:
        Wa = 0

    # -------- B --------
    Tb, _ = B_air.measure()
    Twb, _ = B_wat.measure()
    try:
        Db = B_dist.read()
    except:
        Db = 0

    # -------- C --------
    Tc, _ = C_air.measure()
    Twc, _ = C_wat.measure()
    try:
        Dc = C_dist.read()
    except:
        Dc = 0

    # -------- D --------
    UV = uv_d.read_uv()
    full, IR = tsl_d.get_raw_luminosity()
    LUX = tsl_d.calculate_lux(full, IR)

    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4

    # -------- PRINT --------
    print("-"*60)
    print("A | T_air:", Ta, "T_wat:", Tw, "Dist:", Da, "Weight:", round(Wa,1))
    print("B | T_air:", Tb, "T_wat:", Twb, "Dist:", Db)
    print("C | T_air:", Tc, "T_wat:", Twc, "Dist:", Dc)
    print("D | UV:", UV, "IR:", IR, "LUX:", LUX, "WIND:", WIND)

    # -------- SEND --------
    send_ts(API_A, {1: Ta, 2: Tw, 3: Da, 4: Wa})
    send_ts(API_B, {1: Tb, 2: Twb, 3: Db})
    send_ts(API_C, {1: Tc, 2: Twc, 3: Dc})
    send_ts(API_D, {1: WIND, 2: UV, 3: LUX, 4: IR})

    # -------- AUTO RESET --------
    if time.time() - start_time > AUTO_RESET_SEC:
        print("Auto reset for OTA...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(SEND_INTERVAL)
