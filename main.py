# ==================================================
# main.py — Models A + B + C + D
# ThingSpeak + Weight + VL53 Calibration
# ==================================================

import time, gc, machine
from machine import Pin, SoftI2C
import urequests

# ---------------- ThingSpeak KEYS ----------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

# ---------------- ThingSpeak SEND ----------------
def send_ts(api, f1, f2=None, f3=None, f4=None):
    url = "https://api.thingspeak.com/update?api_key={}&field1={}".format(api, f1)
    if f2 is not None: url += "&field2={}".format(f2)
    if f3 is not None: url += "&field3={}".format(f3)
    if f4 is not None: url += "&field4={}".format(f4)

    try:
        r = urequests.get(url)
        print("TS:", r.status_code, r.text)
        r.close()
    except Exception as e:
        print("TS ERROR:", e)

# ---------------- I2C MAP ----------------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ---------------- LIBRARIES ----------------
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.hx711_clean import HX711

# ---------------- SENSORS ----------------
# Model A
A_air  = SHT30(i2cA, 0x45)
A_wat  = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)

# Model B
B_air  = SHT30(i2cB, 0x45)
B_wat  = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

# Model C
C_air  = SHT30(i2cC, 0x45)
C_wat  = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

# Model D
D_uv  = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# ---------------- HX711 ----------------
hxA = HX711(dt=34, sck=33)
hxB = HX711(dt=35, sck=33)
hxC = HX711(dt=36, sck=16)

# ---------------- WEIGHT CALIBRATION ----------------


hxA.scale = 447.3984     # A → 5 kg
hxB.scale = 447.3984      # B → unchanged
hxC.scale = 778.7703    # C → 1 kg

hxA.tare(samples=60)
hxB.tare(samples=80)
hxC.tare(samples=60)

# ---------------- VL53L0X CALIBRATION ----------------
K_VL53 = 0.66   # معامل التصحيح المعتمد

def read_distance_cm(vl):
    d_mm = vl.read()
    if d_mm is None:
        return None
    return round((d_mm / 10.0) * K_VL53, 2)

# ---------------- WEIGHT FILTER ----------------
EMA_ALPHA = 0.2
wA = wB = wC = 0.0

def read_weight(hx, samples=15):
    vals = []
    for _ in range(samples):
        vals.append(hx.read())
        time.sleep(0.005)
    vals.sort()
    vals = vals[2:-2]
    avg = sum(vals) / len(vals)
    return (avg - hx.offset) / hx.scale

# ---------------- TIMERS ----------------
tA = tB = tC = tD = tW = time.ticks_ms()

# ---------------- HOURLY RESET ----------------
START_TIME = time.ticks_ms()
ONE_HOUR = 60 * 60 * 1000

print("=== MAIN RUNNING (FINAL + VL53 CAL) ===")

# ================= MAIN LOOP =================
while True:
    now = time.ticks_ms()

    # ---- Weight update (2s) ----
    if time.ticks_diff(now, tW) > 2000:
        wA = EMA_ALPHA * read_weight(hxA) + (1 - EMA_ALPHA) * wA
        wB = EMA_ALPHA * read_weight(hxB) + (1 - EMA_ALPHA) * wB
        wC = EMA_ALPHA * read_weight(hxC) + (1 - EMA_ALPHA) * wC
        tW = now

    # ---- Model A (20s) ----
    if time.ticks_diff(now, tA) > 20000:
        Ta,_  = A_air.measure()
        Twa,_ = A_wat.measure()
        Da = read_distance_cm(A_dist)
        send_ts(API_A, round(Ta,2), round(Twa,2), Da, round(wA,2))
        tA = now

    # ---- Model B (20s) ----
    if time.ticks_diff(now, tB) > 20000:
        Tb,_  = B_air.measure()
        Twb,_ = B_wat.measure()
        Db = read_distance_cm(B_dist)
        send_ts(API_B, round(Tb,2), round(Twb,2), Db, round(wB,2))
        tB = now

    # ---- Model C (20s) ----
    if time.ticks_diff(now, tC) > 20000:
        Tc,_  = C_air.measure()
        Twc,_ = C_wat.measure()
        Dc = read_distance_cm(C_dist)
        send_ts(API_C, round(Tc,2), round(Twc,2), Dc, round(wC,2))
        tC = now

    # ---- Model D (5 min) ----
    if time.ticks_diff(now, tD) > 300000:
        UV = D_uv.read_uv()
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)
        send_ts(API_D, UV, ir, round(lux,1))
        tD = now

    # ---- Hourly reset ----
    if time.ticks_diff(now, START_TIME) > ONE_HOUR:
        print("Hourly reset")
        time.sleep(2)
        machine.reset()

    gc.collect()
