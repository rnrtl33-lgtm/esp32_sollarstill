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
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)

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

print("=== SYSTEM START ===")

# ================= MAIN LOOP =================
while True:
    try:
        # ---------- READ A ----------
        TaA,_ = A_air.measure()
        TwA,_ = A_wat.measure()
        dA = None
        try:
            dA = (A_dist.read()/10)*CAL_A + OFF_A
        except:
            pass

        # ---------- READ B ----------
        TaB,_ = B_air.measure()
        TwB,_ = B_wat.measure()
        dB = None
        try:
            dB = (B_dist.read()/10)*CAL_B + OFF_B
        except:
            pass

        # ---------- READ C ----------
        TaC,_ = C_air.measure()
        TwC,_ = C_wat.measure()
        dC = None
        try:
            dC = (C_dist.read()/10)*CAL_C + OFF_C
        except:
            pass

        # ---------- READ D ----------
        try:
            UV = D_uv.read_uv()
            full, ir = D_lux.get_raw_luminosity()
            lux = D_lux.calculate_lux(full, ir)
        except:
            UV, lux, ir = None, None, None

        # ---------- PRINT FIRST ----------
        print("\n----- SENSOR READINGS -----")
        print("A | Ta:", round(TaA,2), "Tw:", round(TwA,2),
              "Dist:", round(dA,2) if dA is not None else "--", "cm")
        print("B | Ta:", round(TaB,2), "Tw:", round(TwB,2),
              "Dist:", round(dB,2) if dB is not None else "--", "cm")
        print("C | Ta:", round(TaC,2), "Tw:", round(TwC,2),
              "Dist:", round(dC,2) if dC is not None else "--", "cm")
        print("D | UV:", UV if UV is not None else "--",
              "Lux:", lux if lux is not None else "--",
              "IR:", ir if ir is not None else "--")
        print("---------------------------")

        # ---------- SEND AFTER PRINT ----------
        send_ts(API_A, round(TaA,2), round(TwA,2), round(dA,2) if dA else 0)
        send_ts(API_B, round(TaB,2), round(TwB,2), round(dB,2) if dB else 0)
        send_ts(API_C, round(TaC,2), round(TwC,2), round(dC,2) if dC else 0)
        send_ts(API_D,
                round(UV,2) if UV else 0,
                round(lux,2) if lux else 0,
                ir if ir else 0)

        gc.collect()

    except Exception as e:
        print("UNEXPECTED ERROR:", e)

    time.sleep(10)
