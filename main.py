# ================= main.py =================
import time, gc
from machine import Pin, SoftI2C
import urequests

# ---------- ThingSpeak ----------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, f1, f2, f3=None, f4=None):
    url = "http://api.thingspeak.com/update?api_key={}&field1={}&field2={}".format(api, f1, f2)
    if f3 is not None:
        url += "&field3={}".format(f3)
    if f4 is not None:
        url += "&field4={}".format(f4)

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
from hx711_clean import HX711

# ---------- Sensors ----------
A_air, A_wat, A_dist = SHT30(i2cA,0x45), SHT30(i2cA,0x44), VL53L0X(i2cA)
B_air, B_wat, B_dist = SHT30(i2cB,0x45), SHT30(i2cB,0x44), VL53L0X(i2cB)
C_air, C_wat, C_dist = SHT30(i2cC,0x45), SHT30(i2cC,0x44), VL53L0X(i2cC)
D_uv, D_lux = LTR390(i2cD), TSL2591(i2cD)

# ---------- HX711 (Model A) ----------
hx = HX711(dt=34, sck=33)
hx.scale = 778.7703
hx.tare(samples=60)

# ---------- Weight Processing ----------
EMA_ALPHA = 0.2        # نعومة القراءة
WEIGHT_DELTA = 15.0    # تغير حقيقي
weight_ema = 0.0
last_sent_weight = 0.0

def read_weight_raw(samples=15):
    vals = []
    for _ in range(samples):
        vals.append(hx.read())
        time.sleep(0.005)
    vals.sort()
    vals = vals[2:-2] if len(vals) > 6 else vals
    avg = sum(vals) / len(vals)
    return (avg - hx.offset) / hx.scale

# ---------- Timers ----------
t_weight = time.ticks_ms()
t_A = time.ticks_ms()
t_B = time.ticks_ms()
t_C = time.ticks_ms()
t_D = time.ticks_ms()

print("=== MAIN RUNNING (IMPROVED) ===")

while True:
    now = time.ticks_ms()

    # ===== Weight (every 2s) =====
    if time.ticks_diff(now, t_weight) > 2000:
        w = read_weight_raw()
        weight_ema = (EMA_ALPHA * w) + (1 - EMA_ALPHA) * weight_ema

        if abs(weight_ema - last_sent_weight) >= WEIGHT_DELTA:
            print("W(A): {:.1f} g (changed)".format(weight_ema))
            last_sent_weight = weight_ema
        else:
            print("W(A): {:.1f} g".format(weight_ema))

        t_weight = now

    # ===== A (every 20s) =====
    if time.ticks_diff(now, t_A) > 20000:
        Ta,_ = A_air.measure()
        Twa,_ = A_wat.measure()
        Da = A_dist.read()

        print("A:", round(Ta,2), round(Twa,2), Da, "W:", round(weight_ema,1))
        send_ts(API_A, round(Ta,2), round(Twa,2), Da, round(weight_ema,1))
        t_A = now

    # ===== B (every 20s) =====
    if time.ticks_diff(now, t_B) > 20000:
        Tb,_ = B_air.measure()
        Twb,_ = B_wat.measure()
        Db = B_dist.read()
        print("B:", round(Tb,2), round(Twb,2), Db)
        send_ts(API_B, round(Tb,2), round(Twb,2), Db)
        t_B = now

    # ===== C (every 20s) =====
    if time.ticks_diff(now, t_C) > 20000:
        Tc,_ = C_air.measure()
        Twc,_ = C_wat.measure()
        Dc = C_dist.read()
        print("C:", round(Tc,2), round(Twc,2), Dc)
        send_ts(API_C, round(Tc,2), round(Twc,2), Dc)
        t_C = now

    # ===== D (every 5 min) =====
    if time.ticks_diff(now, t_D) > 300000:
        UV = D_uv.read_uv()
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)
        print("D:", UV, ir, round(lux,1))
        send_ts(API_D, UV, ir, round(lux,1))
        t_D = now

    gc.collect()

