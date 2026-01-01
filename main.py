# =====================================================
# ESP32 SENSOR SYSTEM
# A,B: Temp + Distance + Weight
# C  : Temp + Distance
# D  : UV + LUX + IR   (SCL = GPIO16)
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

def send_ts(api, f1, f2, f3, f4=None):
    try:
        url = f"https://api.thingspeak.com/update?api_key={api}"
        url += f"&field1={f1}&field2={f2}&field3={f3}"
        if f4 is not None:
            url += f"&field4={f4}"
        r = urequests.get(url)
        r.close()
        print("TS SENT:", api, f1, f2, f3, f4)
    except Exception as e:
        print("TS ERROR:", e)

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
    print("WiFi connected:", wlan.isconnected())

connect_wifi()

# ================= LIBS =================
from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.hx711 import HX711
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591

# ================= I2C BUSSES =================
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(16))   # ✅ تم التعديل هنا

# ================= SENSORS =================
# --- Model A ---
A_out = SHT30(i2cA, 0x45)
A_in  = SHT30(i2cA, 0x44)
A_dis = VL53L0X(i2cA)

# --- Model B ---
B_out = SHT30(i2cB, 0x45)
B_in  = SHT30(i2cB, 0x44)
B_dis = VL53L0X(i2cB)

# --- Model C ---
C_out = SHT30(i2cC, 0x45)
C_in  = SHT30(i2cC, 0x44)
C_dis = VL53L0X(i2cC)

# --- Model D ---
D_uv  = LTR390(i2cD)
D_lux = TSL2591(i2cD)

# ================= INIT MODEL D (CRITICAL) =================
# --- TSL2591 ---
D_lux.enable()
D_lux.set_gain(TSL2591.GAIN_MED)
D_lux.set_timing(TSL2591.INTEGRATIONTIME_200MS)
time.sleep_ms(400)

# --- LTR390 ---
D_uv.set_mode_uv()
time.sleep_ms(100)

# ================= WEIGHT =================
# --- Model A ---
hxA = HX711(dt=34, sck=33)
hxA.offset = 46770.14
hxA.scale  = 410.05076

# --- Model B ---
hxB = HX711(dt=35, sck=17)
hxB.offset = 24163.08
hxB.scale  = 416.56064

# ================= TIMING =================
READ_DELAY    = 2
SEND_INTERVAL = 30
last_send = time.time()

print("\n=== SYSTEM STARTED (GPIO16 FIXED – FINAL MODE) ===\n")

# ================= MAIN LOOP =================
while True:
    try:
        # -------- Model A --------
        Ta_out,_ = A_out.measure()
        Ta_in,_  = A_in.measure()
        Da = A_dis.read() or 0
        Wa = max(0, (hxA.read() - hxA.offset) / hxA.scale)
        time.sleep_ms(80)

        # -------- Model B --------
        Tb_out,_ = B_out.measure()
        Tb_in,_  = B_in.measure()
        Db = B_dis.read() or 0
        Wb = max(0, (hxB.read() - hxB.offset) / hxB.scale)
        time.sleep_ms(80)

        # -------- Model C --------
        Tc_out,_ = C_out.measure()
        Tc_in,_  = C_in.measure()
        Dc = C_dis.read() or 0
        time.sleep_ms(80)

        # -------- Model D --------
        UV = D_uv.read_uv()
        time.sleep_ms(50)
        full, ir = D_lux.get_raw_luminosity()
        lux = D_lux.calculate_lux(full, ir)

        # -------- SEND --------
        if time.time() - last_send >= SEND_INTERVAL:

            send_ts(API_A,
                round(Ta_out,2),
                round(Ta_in,2),
                round(Da/10,2),
                round(Wa,1)
            )

            send_ts(API_B,
                round(Tb_out,2),
                round(Tb_in,2),
                round(Db/10,2),
                round(Wb,1)
            )

            send_ts(API_C,
                round(Tc_out,2),
                round(Tc_in,2),
                round(Dc/10,2)
            )

            send_ts(API_D,
                round(UV,2),
                round(lux,2),
                round(ir,2)
            )

            last_send = time.time()
            gc.collect()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(READ_DELAY)
