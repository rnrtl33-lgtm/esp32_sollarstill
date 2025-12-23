import time, gc, machine
from machine import Pin, SoftI2C
import network, urequests

# ================= WIFI =================
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qtn7tu3"

# ================= STOP BUTTON =================
STOP_BTN = Pin(0, Pin.IN, Pin.PULL_UP)
def check_stop():
    if not STOP_BTN.value():
        machine.reset()

# ================= THINGSPEAK =================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, f1, f2=None, f3=None):
    url = "https://api.thingspeak.com/update?api_key={}&field1={}".format(api, f1)
    if f2 is not None: url += "&field2={}".format(f2)
    if f3 is not None: url += "&field3={}".format(f3)
    try:
        r = urequests.get(url)
        r.close()
    except:
        pass

# ================= OTA =================
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "rnrtl33-lgtm/esp32_sollarstill/main/main.py"
)

OTA_DONE = False
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        t = 15
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    return wlan.isconnected()

def ota_check():
    global OTA_DONE
    if OTA_DONE: return
    try:
        r = urequests.get(GITHUB_RAW_URL)
        new = r.text
        r.close()
        with open("main.py") as f:
            old = f.read()
        if new != old:
            with open("main.py","w") as f:
                f.write(new)
            OTA_DONE = True
            machine.reset()
    except:
        pass

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

# ================= INIT =================
K_VL53 = 0.66
CYCLE_DELAY = 30          # 30 ثانية بين كل دورة
SEND_INTERVAL = 5*60      # 5 دقائق
CYCLES_REQUIRED = 3

A = {"Ta":0,"Tw":0,"D":0,"n":0}
B = {"Ta":0,"Tw":0,"D":0,"n":0}
C = {"Ta":0,"Tw":0,"D":0,"n":0}
Dsum = {"UV":0,"LUX":0,"IR":0,"n":0}

last_send = time.time()
cycle_index = 0   # 0=A, 1=B, 2=C, 3=D

# ================= START =================
if connect_wifi():
    ota_check()

time.sleep(2)

# ================= MAIN LOOP =================
while True:
    machine.idle()
    check_stop()

    try:
        # ===== CYCLE A =====
        if cycle_index == 0:
            Ta,_ = A_air.measure()
            Tw,_ = A_wat.measure()
            d = A_dist.read()
            if d: A["D"] += (d/10)*K_VL53
            A["Ta"]+=Ta; A["Tw"]+=Tw; A["n"]+=1

        # ===== CYCLE B =====
        elif cycle_index == 1:
            Ta,_ = B_air.measure()
            Tw,_ = B_wat.measure()
            d = B_dist.read()
            if d: B["D"] += (d/10)*K_VL53
            B["Ta"]+=Ta; B["Tw"]+=Tw; B["n"]+=1

        # ===== CYCLE C =====
        elif cycle_index == 2:
            Ta,_ = C_air.measure()
            Tw,_ = C_wat.measure()
            d = C_dist.read()
            if d: C["D"] += (d/10)*K_VL53
            C["Ta"]+=Ta; C["Tw"]+=Tw; C["n"]+=1

        # ===== CYCLE D =====
        else:
            UV = D_uv.read_uv()
            full, ir = D_lux.get_raw_luminosity()
            lux = D_lux.calculate_lux(full, ir)
            Dsum["UV"]+=UV; Dsum["LUX"]+=lux; Dsum["IR"]+=ir; Dsum["n"]+=1

    except:
        pass

    cycle_index = (cycle_index + 1) % 4
    time.sleep(CYCLE_DELAY)

    # ===== SEND CONDITION =====
    if (
        time.time() - last_send >= SEND_INTERVAL and
        A["n"] >= CYCLES_REQUIRED and
        B["n"] >= CYCLES_REQUIRED and
        C["n"] >= CYCLES_REQUIRED
    ):
        send_ts(API_A, round(A["Ta"]/A["n"],2), round(A["Tw"]/A["n"],2), round(A["D"]/A["n"],2))
        send_ts(API_B, round(B["Ta"]/B["n"],2), round(B["Tw"]/B["n"],2), round(B["D"]/B["n"],2))
        send_ts(API_C, round(C["Ta"]/C["n"],2), round(C["Tw"]/C["n"],2), round(C["D"]/C["n"],2))
        send_ts(API_D, round(Dsum["UV"]/Dsum["n"],2), round(Dsum["LUX"]/Dsum["n"],2), round(Dsum["IR"]/Dsum["n"],2))

        A.update({"Ta":0,"Tw":0,"D":0,"n":0})
        B.update({"Ta":0,"Tw":0,"D":0,"n":0})
        C.update({"Ta":0,"Tw":0,"D":0,"n":0})
        Dsum.update({"UV":0,"LUX":0,"IR":0,"n":0})

        last_send = time.time()
        gc.collect()
