import time, gc, machine
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
        print("TS SENT:", api, f1, f2, f3)
    except Exception as e:
        print("TS ERROR:", e)

# ================= WIFI =================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        t = 20
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    print("WiFi connected:", wlan.isconnected())

connect_wifi()

# ================= LIBS =================
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591

# ================= I2C INIT =================
def init_i2c_and_sensors():
    global i2cA, i2cB, i2cC, i2cD
    global A_air, A_wat, A_dist
    global B_air, B_wat, B_dist
    global C_air, C_wat, C_dist
    global D_uv, D_lux

    print("Reinitializing I2C & sensors...")

    i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
    i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
    i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
    i2cD = SoftI2C(sda=Pin(15), scl=Pin(16))

    # --- Model A ---
    A_air  = SHT30(i2cA, 0x45)
    A_wat  = SHT30(i2cA, 0x44)
    A_dist = VL53L0X(i2cA)

    # --- Model B ---
    B_air  = SHT30(i2cB, 0x45)
    B_wat  = SHT30(i2cB, 0x44)
    B_dist = VL53L0X(i2cB)

    # --- Model C ---
    C_air  = SHT30(i2cC, 0x45)
    C_wat  = SHT30(i2cC, 0x44)
    C_dist = VL53L0X(i2cC)

    # --- Model D (محمي) ---
    try:
        D_uv  = LTR390(i2cD)
        D_lux = TSL2591(i2cD)
        print("Model D detected")
    except OSError as e:
        print("Model D NOT detected:", e)
        D_uv = None
        D_lux = None

# أول تهيئة
init_i2c_and_sensors()

# ================= VL53 CAL =================
CAL_A, OFF_A = 1.0, 0.0
CAL_B, OFF_B = 0.90, -0.2
CAL_C, OFF_C = 1.00,  0.0
VL_WARMUP = 3
Aw = Bw = Cw = 0

# ================= PARAMS =================
CYCLE_DELAY   = 3
SEND_INTERVAL = 15
RESET_ON_ERR  = 5

# ================= STORAGE =================
A = {"Ta":0,"Tw":0,"D":0,"n":0}
B = {"Ta":0,"Tw":0,"D":0,"n":0}
C = {"Ta":0,"Tw":0,"D":0,"n":0}
Dsum = {"UV":0,"LUX":0,"IR":0,"n":0}

cycle_index = 0
last_send = time.time()
err_count = 0

print("\n=== SYSTEM STARTED (SAFE MODE WITH MODEL D PROTECTION) ===\n")

# ================= MAIN LOOP =================
while True:
    try:
        # ---------- A ----------
        if cycle_index == 0:
            Ta,_ = A_air.measure()
            Tw,_ = A_wat.measure()
            d = A_dist.read()
            if d:
                Aw += 1
                if Aw > VL_WARMUP:
                    A["D"] += (d/10)*CAL_A + OFF_A
            A["Ta"] += Ta; A["Tw"] += Tw; A["n"] += 1

        # ---------- B ----------
        elif cycle_index == 1:
            Ta,_ = B_air.measure()
            Tw,_ = B_wat.measure()
            d = B_dist.read()
            if d:
                Bw += 1
                if Bw > VL_WARMUP:
                    B["D"] += (d/10)*CAL_B + OFF_B
            B["Ta"] += Ta; B["Tw"] += Tw; B["n"] += 1

        # ---------- C ----------
        elif cycle_index == 2:
            Ta,_ = C_air.measure()
            Tw,_ = C_wat.measure()
            d = C_dist.read()
            if d:
                Cw += 1
                if Cw > VL_WARMUP:
                    C["D"] += (d/10)*CAL_C + OFF_C
            C["Ta"] += Ta; C["Tw"] += Tw; C["n"] += 1

        # ---------- D ----------
        else:
            if D_uv and D_lux:
                UV = D_uv.read_uv()
                full, ir = D_lux.get_raw_luminosity()
                lux = D_lux.calculate_lux(full, ir)
                Dsum["UV"]+=UV; Dsum["LUX"]+=lux; Dsum["IR"]+=ir; Dsum["n"]+=1

        err_count = 0

    except OSError as e:
        print("I2C ERROR:", e)
        err_count += 1
        init_i2c_and_sensors()
        time.sleep(0.5)
        if err_count >= RESET_ON_ERR:
            print("Too many I2C errors → RESET")
            time.sleep(2)
            machine.reset()

    cycle_index = (cycle_index + 1) % 4
    time.sleep(CYCLE_DELAY)

    # ================= SEND =================
    if time.time() - last_send >= SEND_INTERVAL:
        print("=== SENDING DATA ===")

        if A["n"]:
            send_ts(API_A,
                round(A["Ta"]/A["n"],2),
                round(A["Tw"]/A["n"],2),
                round(A["D"]/max(A["n"],1),2)
            )

        if B["n"]:
            send_ts(API_B,
                round(B["Ta"]/B["n"],2),
                round(B["Tw"]/B["n"],2),
                round(B["D"]/max(B["n"],1),2)
            )

        if C["n"]:
            send_ts(API_C,
                round(C["Ta"]/C["n"],2),
                round(C["Tw"]/C["n"],2),
                round(C["D"]/max(C["n"],1),2)
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


    
