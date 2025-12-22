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
        gc.collect()                      # <<< FIX 1
    except Exception as e:
        print("TS ERROR:", e)
        gc.collect()                      # <<< FIX 1

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
A_air, A_wat, A_dist = SHT30(i2cA,0x45), SHT30(i2cA,0x44), VL53L0X(i2cA)
B_air, B_wat, B_dist = SHT30(i2cB,0x45), SHT30(i2cB,0x44), VL53L0X(i2cB)
C_air, C_wat, C_dist = SHT30(i2cC,0x45), SHT30(i2cC,0x44), VL53L0X(i2cC)

D_uv  = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# ---------------- HX711 ----------------
hxA = HX711(dt=34, sck=33)
hxB = HX711(dt=35, sck=33)
hxC = HX711(dt=36, sck=16)

hxA.scale = 447.3984
hxB.scale = 447.3984
hxC.scale = 778.7703

hxA.tare(60)
hxB.tare(60)
hxC.tare(60)

# ---------------- VL53 CAL ----------------
K_VL53 = 0.66
def read_distance_cm(vl):
    try:                                 # <<< FIX 3
        d = vl.read()
        return None if d is None else round((d/10)*K_VL53,2)
    except:
        return None

# ---------------- WEIGHT ----------------
def read_weight(hx, n=15):
    try:                                 # <<< FIX 3
        vals = [hx.read() for _ in range(n)]
        vals.sort()
        vals = vals[2:-2]
        w = (sum(vals)/len(vals) - hx.offset) / hx.scale
        if abs(w) < 0.05:                # <<< FIX 4
            hx.tare(30)
        return w
    except:
        return None

# ---------------- AVERAGING (5 MIN) ----------------
A = {"Ta":0,"Tw":0,"D":0,"W":0,"n":0}
B = {"Ta":0,"Tw":0,"D":0,"W":0,"n":0}
C = {"Ta":0,"Tw":0,"D":0,"W":0,"n":0}

Dsum={"wind":0,"UV":0,"LUX":0,"IR":0,"n":0}

SEND_INTERVAL = 5*60*1000
last_send = time.ticks_ms()

# ---------------- RESET TIMER ----------------
START_TIME = time.ticks_ms()             # <<< FIX 5
RESET_INTERVAL = 6*60*60*1000             # 6 hours

print("=== MAIN RUNNING (FINAL / STABLE) ===")

# ================= MAIN LOOP =================
while True:

    for S,air,wat,dist,hx in [
        (A,A_air,A_wat,A_dist,hxA),
        (B,B_air,B_wat,B_dist,hxB),
        (C,C_air,C_wat,C_dist,hxC)
    ]:
        try:
            Ta,_ = air.measure()
            Tw,_ = wat.measure()
            Dm = read_distance_cm(dist)
            W  = read_weight(hx)

            if Ta is not None and Tw is not None:   # <<< FIX 2
                S["Ta"]+=Ta; S["Tw"]+=Tw
                if Dm is not None: S["D"]+=Dm
                if W  is not None: S["W"]+=W
                S["n"]+=1
        except:
            pass

    try:
        UV = D_uv.read_uv()
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)

        Dsum["wind"]+=0
        Dsum["UV"]+=UV
        Dsum["LUX"]+=lux
        Dsum["IR"]+=ir
        Dsum["n"]+=1
    except:
        pass

    if time.ticks_diff(time.ticks_ms(), last_send) > SEND_INTERVAL:
        for api,S in [(API_A,A),(API_B,B),(API_C,C)]:
            if S["n"] > 0:
                send_ts(api,
                    round(S["Ta"]/S["n"],2),
                    round(S["Tw"]/S["n"],2),
                    round(S["D"]/S["n"],2),
                    round(S["W"]/S["n"],2)
                )
            S.update({"Ta":0,"Tw":0,"D":0,"W":0,"n":0})

        if Dsum["n"] > 0:
            send_ts(API_D,
                round(Dsum["wind"]/Dsum["n"],2),
                round(Dsum["UV"]/Dsum["n"],2),
                round(Dsum["LUX"]/Dsum["n"],2),
                round(Dsum["IR"]/Dsum["n"],2)
            )
        Dsum.update({"wind":0,"UV":0,"LUX":0,"IR":0,"n":0})

        last_send = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), START_TIME) > RESET_INTERVAL:   # <<< FIX 5
        print("SAFE RESET")
        time.sleep(2)
        machine.reset()

    gc.collect()
    time.sleep(5)
