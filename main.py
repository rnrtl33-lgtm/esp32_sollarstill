import time, gc
from machine import Pin, SoftI2C
import network, urequests

# ================= WIFI =================
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qtn7tu3"

# ================= THINGSPEAK =================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, f1, f2, f3):
    try:
        url = (
            "https://api.thingspeak.com/update?"
            "api_key={}&field1={}&field2={}&field3={}"
        ).format(api, f1, f2, f3)
        r = urequests.get(url)
        r.close()
    except:
        pass

# ================= WIFI CONNECT =================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        t = 20
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    return wlan.isconnected()

connect_wifi()

# ================= I2C =================
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ================= LIBS =================
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591

# ================= SENSORS =================
A_air, A_wat, A_dist = SHT30(i2cA,0x45), SHT30(i2cA,0x44), VL53L0X(i2cA)
B_air, B_wat, B_dist = SHT30(i2cB,0x45), SHT30(i2cB,0x44), VL53L0X(i2cB)
C_air, C_wat, C_dist = SHT30(i2cC,0x45), SHT30(i2cC,0x44), VL53L0X(i2cC)
D_uv  = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# ================= VL53L0X CALIBRATION =================
CAL_A, OFF_A = 0.74, -0.3
CAL_B, OFF_B = 0.90, -0.2
CAL_C, OFF_C = 1.00,  0.0

VL_WARMUP = 3
Aw = Bw = Cw = 0

# ================= PARAMS =================
CYCLE_DELAY = 3
SEND_INTERVAL = 10

# ================= STORAGE =================
A = {"Ta":0,"Tw":0,"D":0,"n":0}
B = {"Ta":0,"Tw":0,"D":0,"n":0}
C = {"Ta":0,"Tw":0,"D":0,"n":0}
Dsum = {"UV":0,"LUX":0,"IR":0,"n":0}

# آخر قراءة صحيحة
A_last = None
B_last = None
C_last = None

cycle_index = 0
last_send = time.time()

print("=== SYSTEM RUNNING (CLEAN DISPLAY MODE) ===")

# ================= MAIN LOOP =================
while True:
    try:
        # ---------- MODEL A ----------
        if cycle_index == 0:
            Ta,_ = A_air.measure()
            Tw,_ = A_wat.measure()
            try:
                d = A_dist.read()
            except:
                d = None

            if d:
                Aw += 1
                if Aw > VL_WARMUP:
                    A_last = (d/10)*CAL_A + OFF_A
                    A["D"] += A_last

            A["Ta"] += Ta
            A["Tw"] += Tw
            A["n"]  += 1

        # ---------- MODEL B ----------
        elif cycle_index == 1:
            Ta,_ = B_air.measure()
            Tw,_ = B_wat.measure()
            d = B_dist.read()

            if d:
                Bw += 1
                if Bw > VL_WARMUP:
                    B_last = (d/10)*CAL_B + OFF_B
                    B["D"] += B_last

            B["Ta"] += Ta
            B["Tw"] += Tw
            B["n"]  += 1

        # ---------- MODEL C ----------
        elif cycle_index == 2:
            Ta,_ = C_air.measure()
            Tw,_ = C_wat.measure()
            d = C_dist.read()

            if d:
                Cw += 1
                if Cw > VL_WARMUP:
                    C_last = (d/10)*CAL_C + OFF_C
                    C["D"] += C_last

            C["Ta"] += Ta
            C["Tw"] += Tw
            C["n"]  += 1

        # ---------- MODEL D ----------
        else:
            UV = D_uv.read_uv()
            full, ir = D_lux.get_raw_luminosity()
            lux = D_lux.calculate_lux(full, ir)

            Dsum["UV"]  += UV
            Dsum["LUX"] += lux
            Dsum["IR"]  += ir
            Dsum["n"]   += 1

    except:
        pass

    cycle_index = (cycle_index + 1) % 4
    time.sleep(CYCLE_DELAY)

    # ---------- DISPLAY ----------
    print("\n----- SENSOR SNAPSHOT -----")
    print("Model A Distance:", round(A_last,2) if A_last is not None else "--", "cm")
    print("Model B Distance:", round(B_last,2) if B_last is not None else "--", "cm")
    print("Model C Distance:", round(C_last,2) if C_last is not None else "--", "cm")
    print("---------------------------")

    # ---------- SEND ----------
    if time.time() - last_send >= SEND_INTERVAL:
        if A["n"]:
            send_ts(API_A,
                round(A["Ta"]/A["n"],2),
                round(A["Tw"]/A["n"],2),
                round(A["D"]/A["n"],2)
            )
        if B["n"]:
            send_ts(API_B,
                round(B["Ta"]/B["n"],2),
                round(B["Tw"]/B["n"],2),
                round(B["D"]/B["n"],2)
            )
        if C["n"]:
            send_ts(API_C,
                round(C["Ta"]/C["n"],2),
                round(C["Tw"]/C["n"],2),
                round(C["D"]/C["n"],2)
            )
        if Dsum["n"]:
            send_ts(API_D,
                round(Dsum["UV"]/Dsum["n"],2),
                round(Dsum["LUX"]/Dsum["n"],2),
                round(Dsum["IR"]/Dsum["n"],2)
            )

        A.update({"Ta":0,"Tw":0,"D":0,"n":0})
        B.update({"Ta":0,"Tw":0,"D":0,"n":0})
        C.update({"Ta":0,"Tw":0,"D":0,"n":0})
        Dsum.update({"UV":0,"LUX":0,"IR":0,"n":0})

        last_send = time.time()
        gc.collect()
