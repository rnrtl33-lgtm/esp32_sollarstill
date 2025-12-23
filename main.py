import time, gc, machine
from machine import Pin, SoftI2C
import network, urequests

# ================= WIFI =================
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qtn7tu3"

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "rnrtl33-lgtm/esp32_sollarstill/main/main.py"
)

OTA_DONE = False   # يمنع loop

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("WIFI: Connecting...")
        wlan.connect(SSID, PASSWORD)
        t = 15
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    return wlan.isconnected()

def ota_check():
    global OTA_DONE
    if OTA_DONE:
        return
    try:
        print("OTA: Checking...")
        r = urequests.get(GITHUB_RAW_URL)
        new_code = r.text
        r.close()

        with open("main.py", "r") as f:
            old_code = f.read()

        if new_code != old_code:
            print("OTA: New version found")
            with open("main.py", "w") as f:
                f.write(new_code)

            OTA_DONE = True
            print("OTA: Resetting...")
            time.sleep(2)
            machine.reset()
        else:
            print("OTA: No update")
    except Exception as e:
        print("OTA ERROR:", e)

# ================= I2C MAP =================
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

# ================= LIBRARIES =================
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
laser_index = 0

print("=== SYSTEM START ===")

# ---- WIFI + OTA ONCE ----
if connect_wifi():
    ota_check()

print("=== SENSOR LOOP ===")
print("VL53: WARM UP...")
time.sleep(2)        # حل (3): وقت استقرار الليزر

# ================= MAIN LOOP =================
while True:
    try:
        # ---- SHT30 ----
        TaA,_ = A_air.measure()
        TwA,_ = A_wat.measure()
        TaB,_ = B_air.measure()
        TwB,_ = B_wat.measure()
        TaC,_ = C_air.measure()
        TwC,_ = C_wat.measure()

        DA = DB = DC = None

        # ---- ONE LASER PER CYCLE (حل 2) ----
        if laser_index == 0:
            d = A_dist.read()
            if d is None or d == 0:
                time.sleep_ms(50)
                d = A_dist.read()
            DA = None if d is None else round((d/10)*K_VL53,2)
            active = "A"

        elif laser_index == 1:
            d = B_dist.read()
            if d is None or d == 0:
                time.sleep_ms(50)
                d = B_dist.read()
            DB = None if d is None else round((d/10)*K_VL53,2)
            active = "B"

        else:
            d = C_dist.read()
            if d is None or d == 0:
                time.sleep_ms(50)
                d = C_dist.read()
            DC = None if d is None else round((d/10)*K_VL53,2)
            active = "C"

        laser_index = (laser_index + 1) % 3

        # ---- LIGHT ----
        UV = D_uv.read_uv()
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)

        # ---- PRINT ----
        print("ACTIVE LASER:", active)
        print("A | Ta:",TaA,"Tw:",TwA,"D:",DA)
        print("B | Ta:",TaB,"Tw:",TwB,"D:",DB)
        print("C | Ta:",TaC,"Tw:",TwC,"D:",DC)
        print("D | UV:",UV,"LUX:",lux,"IR:",ir)
        print("-"*45)

    except Exception as e:
        print("ERR:", e)

    gc.collect()
    time.sleep(2)     # حل (4): منع idle الطويل
