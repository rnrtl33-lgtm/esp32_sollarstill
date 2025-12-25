# =====================================================
# ESP32 MULTI-SENSOR SYSTEM
# PRINT TO THONNY + SEND TO THINGSPEAK
# =====================================================

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

# ================= WIFI CONNECT =================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    print("WiFi connected:", wlan.isconnected())
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
UV_sensor  = LTR390(i2cD)
LIGHT_sensor = TSL2591(i2cD)

# ================= VL53L0X CAL =================
CAL_A = 0.6
CAL_B = 0.7077
CAL_C = 0.92

# ================= SEND =================
def send_ts(api, f1, f2, f3):
    try:
        url = (
            "https://api.thingspeak.com/update?"
            "api_key={}&field1={}&field2={}&field3={}"
        ).format(api, f1, f2, f3)
        r = urequests.get(url)
        r.close()
        print("TS SENT:", api)
    except Exception as e:
        print("TS ERROR:", e)

# ================= MAIN LOOP =================
SEND_INTERVAL = 10
last_send = time.time()

print("\n=== SYSTEM STARTED ===\n")

while True:
    try:
        # -------- MODEL A --------
        Ta_A, _ = A_air.measure()
        Tw_A, _ = A_wat.measure()
        dA = A_dist.read()
        dist_A = (dA/10)*CAL_A if dA else 0

        # -------- MODEL B --------
        Ta_B, _ = B_air.measure()
        Tw_B, _ = B_wat.measure()
        dB = B_dist.read()
        dist_B = (dB/10)*CAL_B if dB else 0

        # -------- MODEL C --------
        Ta_C, _ = C_air.measure()
        Tw_C, _ = C_wat.measure()
        dC = C_dist.read()
        dist_C = (dC/10)*CAL_C if dC else 0

        # -------- MODEL D --------
        UV = UV_sensor.read_uv()
        full, ir = LIGHT_sensor.get_raw_luminosity()
        lux = LIGHT_sensor.calculate_lux(full, ir)

        # ========== PRINT TO THONNY ==========
        print("===================================")
        print("Model A | Ta:", round(Ta_A,2),"°C | Tw:",round(Tw_A,2),"°C | D:",round(dist_A,2),"cm")
        print("Model B | Ta:", round(Ta_B,2),"°C | Tw:",round(Tw_B,2),"°C | D:",round(dist_B,2),"cm")
        print("Model C | Ta:", round(Ta_C,2),"°C | Tw:",round(Tw_C,2),"°C | D:",round(dist_C,2),"cm")
        print("UV Index:", round(UV,2))
        print("Light   | Lux:", round(lux,2),"lx | IR:", ir)
        print("===================================\n")

        # ========== SEND ==========
        if time.time() - last_send >= SEND_INTERVAL:
            send_ts(API_A, round(Ta_A,2), round(Tw_A,2), round(dist_A,2))
            send_ts(API_B, round(Ta_B,2), round(Tw_B,2), round(dist_B,2))
            send_ts(API_C, round(Ta_C,2), round(Tw_C,2), round(dist_C,2))
            send_ts(API_D, round(UV,2), round(lux,2), int(ir))
            last_send = time.time()
            gc.collect()

    except Exception as e:
        print("MAIN LOOP ERROR:", e)

    time.sleep(5)
