# ==================================================
# main.py — A + B + C + D
# ThingSpeak SAFE MODE (NO RATE LIMIT)
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

# ---------------- LIBRARIES ----------------
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.hx711_clean import HX711

# ---------------- THINGSPEAK KEYS ----------------
API_A = "PUT_API_A_HERE"
API_B = "PUT_API_B_HERE"
API_C = "PUT_API_C_HERE"
API_D = "PUT_API_D_HERE"

# ---------------- I2C MAP ----------------
# Model A
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
# Model B
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
# Model C
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
# Model D
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ---------------- SENSORS ----------------
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

# ---------------- HX711 CALIB ----------------
hxA.tare()
hxA.scale = 395.6   # ضع رقمك النهائي هنا

# ---------------- WIND ----------------
wind_pulses = 0
wind_pin = Pin(13, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ---------------- TS SEND ----------------
def send_ts(api, data):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        r = urequests.get(url)
        print("TS status:", r.status_code)
        r.close()
    except Exception as e:
        print("TS error:", e)

print("\n=== SYSTEM RUNNING (SAFE TS MODE) ===\n")

# ================= MAIN LOOP =================
while True:

    # ---------- READ A ----------
    Ta, _ = A_air.measure()
    Twa, _ = A_wat.measure()
    try:
        Da = A_dist.read()
    except:
        Da = None
    Wa = hxA.get_weight()

    dataA = {
        "T_air": round(Ta,2),
        "T_wat": round(Twa,2),
        "Dist": Da,
        "Weight": round(Wa,1)
    }

    print("A:", dataA)
    send_ts(API_A, dataA)
    time.sleep(20)   # <<< تأخير حقيقي

    # ---------- READ B ----------
    Tb, _ = B_air.measure()
    Twb, _ = B_wat.measure()
    try:
        Db = B_dist.read()
    except:
        Db = None

    dataB = {
        "T_air": round(Tb,2),
        "T_wat": round(Twb,2),
        "Dist": Db
    }

    print("B:", dataB)
    send_ts(API_B, dataB)
    time.sleep(20)

    # ---------- READ C ----------
    Tc, _ = C_air.measure()
    Twc, _ = C_wat.measure()
    try:
        Dc = C_dist.read()
    except:
        Dc = None

    dataC = {
        "T_air": round(Tc,2),
        "T_wat": round(Twc,2),
        "Dist": Dc
    }

    print("C:", dataC)
    send_ts(API_C, dataC)
    time.sleep(20)

    # ---------- READ D ----------
    UV = D_uv.read_uv()
    full, ir = D_lux.get_raw_luminosity()
    LUX = D_lux.calculate_lux(full, ir)

    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4

    dataD = {
        "UV": UV,
        "IR": ir,
        "LUX": round(LUX,1),
        "WIND": round(WIND,2)
    }

    print("D:", dataD)
    send_ts(API_D, dataD)
    time.sleep(20)

    print("-"*60)
    gc.collect()
