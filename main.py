# ==================================================
# ESP32 Solar Still — MAIN
# A + B + C + D + ThingSpeak
# ==================================================

import time, gc
from machine import Pin, SoftI2C

# ---------------- LIBS ----------------
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.hx711_clean import HX711

# ---------------- THINGSPEAK ----------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, fields):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=" + api
        for i, v in enumerate(fields, start=1):
            url += "&field{}={}".format(i, v)
        r = urequests.get(url)
        print("TS:", r.status_code, r.text)
        r.close()
    except Exception as e:
        print("TS ERROR:", e)

# ---------------- I2C ----------------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ---------------- SENSORS ----------------
A_air = SHT30(i2cA, 0x45)
A_wat = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)
hxA = HX711(34, 33)
hxA.tare()
hxA.scale = 395.6

B_air = SHT30(i2cB, 0x45)
B_wat = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

C_air = SHT30(i2cC, 0x45)
C_wat = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

D_uv = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# ---------------- WIND ----------------
wind_pulses = 0
wind_pin = Pin(13, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

print("\n=== MAIN RUNNING ===\n")

# ================= MAIN LOOP =================
while True:

    # ---------- A ----------
    Ta, _ = A_air.measure()
    Twa, _ = A_wat.measure()
    try:
        Da = A_dist.read()
    except:
        Da = -1
    Wa = hxA.get_weight()

    print("A:", Ta, Twa, Da, Wa)

    if Wa > 0:
        send_ts(API_A, [round(Ta,2), round(Twa,2), Da, round(Wa,1)])

    time.sleep(20)

    # ---------- B ----------
    Tb, _ = B_air.measure()
    Twb, _ = B_wat.measure()
    try:
        Db = B_dist.read()
    except:
        Db = -1

    print("B:", Tb, Twb, Db)
    send_ts(API_B, [round(Tb,2), round(Twb,2), Db])

    time.sleep(20)

    # ---------- C ----------
    Tc, _ = C_air.measure()
    Twc, _ = C_wat.measure()
    try:
        Dc = C_dist.read()
    except:
        Dc = -1

    print("C:", Tc, Twc, Dc)
    send_ts(API_C, [round(Tc,2), round(Twc,2), Dc])

    time.sleep(20)

    # ---------- D ----------
    UV = D_uv.read_uv()
    full, ir = D_lux.get_raw_luminosity()
    lux = D_lux.calculate_lux(full, ir)

    pulses = wind_pulses
    wind_pulses = 0
    wind = pulses * 0.4

    print("D:", UV, ir, lux, wind)
    send_ts(API_D, [UV, ir, round(lux,1), round(wind,2)])

    time.sleep(20)
    gc.collect()
