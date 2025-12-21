# ================= main.py =================
import time, gc
from machine import Pin, SoftI2C
import urequests
from hx711_clean import HX711

# ---------- ThingSpeak ----------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, f1, f2=None, f3=None, f4=None):
    url = "http://api.thingspeak.com/update?api_key={}&field1={}".format(api, f1)
    if f2 is not None: url += "&field2={}".format(f2)
    if f3 is not None: url += "&field3={}".format(f3)
    if f4 is not None: url += "&field4={}".format(f4)
    r = urequests.get(url)
    print("TS:", r.status_code)
    r.close()

# ---------- I2C ----------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591

# ---------- Sensors ----------
A_air, A_wat, A_dist = SHT30(i2cA,0x45), SHT30(i2cA,0x44), VL53L0X(i2cA)
B_air, B_wat, B_dist = SHT30(i2cB,0x45), SHT30(i2cB,0x44), VL53L0X(i2cB)
C_air, C_wat, C_dist = SHT30(i2cC,0x45), SHT30(i2cC,0x44), VL53L0X(i2cC)
D_uv, D_lux = LTR390(i2cD), TSL2591(i2cD)

# =========================================================
# ===================== HX711 =============================
# =========================================================

# ---------- Model A (1kg) ----------
hxA = HX711(dt=34, sck=33)
hxA.scale = 778.7703
hxA.tare(samples=60)

# ---------- Model B (5kg) ----------
hxB = HX711(dt=35, sck=32)
hxB.scale = 447.3984
hxB.tare(samples=80)

# ---------- Model C (5kg) ----------
hxC = HX711(dt=36, sck=25)
hxC.scale = 447.3984
hxC.tare(samples=80)

EMA_ALPHA = 0.2
DELTA_A = 15.0
DELTA_BC = 20.0

wA_ema = wB_ema = wC_ema = 0.0
lastA = lastB = lastC = 0.0

def read_weight(hx, samples=15):
    vals = []
    for _ in range(samples):
        vals.append(hx.read())
        time.sleep(0.005)
    vals.sort()
    if len(vals) > 6:
        vals = vals[2:-2]
    avg = sum(vals) / len(vals)
    return (avg - hx.offset) / hx.scale

# ---------- Timers ----------
tW = tA = tB = tC = tD = time.ticks_ms()

print("=== MAIN RUNNING (A+B+C WEIGHT ENABLED) ===")

while True:
    now = time.ticks_ms()

    # ===== Weight update (2s) =====
    if time.ticks_diff(now, tW) > 2000:
        wA = read_weight(hxA)
        wB = read_weight(hxB)
        wC = read_weight(hxC)

        wA_ema = EMA_ALPHA * wA + (1-EMA_ALPHA) * wA_ema
        wB_ema = EMA_ALPHA * wB + (1-EMA_ALPHA) * wB_ema
        wC_ema = EMA_ALPHA * wC + (1-EMA_ALPHA) * wC_ema

        if abs(wA_ema - lastA) > DELTA_A:
            print("W(A): {:.1f} g".format(wA_ema))
            lastA = wA_ema

        if abs(wB_ema - lastB) > DELTA_BC:
            print("W(B): {:.1f} g".format(wB_ema))
            lastB = wB_ema

        if abs(wC_ema - lastC) > DELTA_BC:
            print("W(C): {:.1f} g".format(wC_ema))
            lastC = wC_ema

        tW = now

    # ===== A (20s) =====
    if time.ticks_diff(now, tA) > 20000:
        Ta,_ = A_air.measure()
        Twa,_ = A_wat.measure()
        Da = A_dist.read()

        send_ts(API_A, round(Ta,2), round(Twa,2), Da, round(wA_ema,1))
        tA = now

    # ===== B (20s) =====
    if time.ticks_diff(now, tB) > 20000:
        Tb,_ = B_air.measure()
        Twb,_ = B_wat.measure()
        Db = B_dist.read()

        send_ts(API_B, round(Tb,2), round(Twb,2), Db, round(wB_ema,1))
        tB = now

    # ===== C (20s) =====
    if time.ticks_diff(now, tC) > 20000:
        Tc,_ = C_air.measure()
        Twc,_ = C_wat.measure()
        Dc = C_dist.read()

        send_ts(API_C, round(Tc,2), round(Twc,2), Dc, round(wC_ema,1))
        tC = now

    # ===== D (5 min) =====
    if time.ticks_diff(now, tD) > 300000:
        UV = D_uv.read_uv()
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)

        send_ts(API_D, UV, ir, round(lux,1))
        tD = now

    gc.collect()
