# ==================================================
# main.py — Unified Models A+B+C+D (STABLE FINAL)
# LTR390: UV ONLY
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

# ===============================
# Libraries (AS-IS, no assumptions)
# ===============================
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X

# ===============================
# ThingSpeak API Keys
# ===============================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# ===============================
# I2C Buses
# ===============================
# Model A
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19), freq=100000)
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23), freq=100000)

# Model B
i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25), freq=100000)
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27), freq=100000)

# Model C
i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32), freq=100000)
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15), freq=100000)

# ===============================
# Sensors Init (SAFE)
# ===============================
# A
A_amb   = SHT30(i2cA1, 0x45)
A_air   = SHT30(i2cA2, 0x45)
A_wat   = SHT30(i2cA2, 0x44)
A_uv    = LTR390(i2cA1)
A_lux   = TSL2591(i2cA2)
A_laser = VL53L0X(i2cA1)

# B
B_air   = SHT30(i2cB2, 0x45)
B_wat   = SHT30(i2cB2, 0x44)
B_uv    = LTR390(i2cB1)
B_lux   = TSL2591(i2cB2)
B_laser = VL53L0X(i2cB1)

# C
C_air   = SHT30(i2cC2, 0x45)
C_wat   = SHT30(i2cC2, 0x44)
C_uv    = LTR390(i2cC1)
C_lux   = TSL2591(i2cC2)
C_laser = VL53L0X(i2cC1)

# ===============================
# Wind Sensor (Model D)
# ===============================
wind_pulses = 0
wind_pin = Pin(4, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ===============================
# Helpers (SAFE READ)
# ===============================
def safe_sht(sensor):
    try:
        time.sleep_ms(60)
        return sensor.measure()
    except:
        return None, None

def safe_uv(sensor):
    try:
        time.sleep_ms(150)   # مهم جدًا
        return sensor.read_uv()
    except:
        return None

def safe_lux(sensor):
    try:
        time.sleep_ms(120)
        full, ir = sensor.get_raw_luminosity()
        lux = sensor.calculate_lux(full, ir)
        return lux, ir
    except:
        return None, None

def safe_dist(sensor):
    try:
        time.sleep_ms(50)
        return sensor.read()
    except:
        return None

# ===============================
# ThingSpeak Sender
# ===============================
def send_ts(api, data):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ===============================
# MAIN LOOP
# ===============================
print("\n>>> MAIN RUNNING (A+B+C+D | UV ONLY) <<<\n")

cycle = 0

while True:

    # ---------- A ----------
    T_amb, H_amb = safe_sht(A_amb)
    T_airA, H_airA = safe_sht(A_air)
    T_watA, H_watA = safe_sht(A_wat)
    UV_A = safe_uv(A_uv)
    LUX_A, IR_A = safe_lux(A_lux)
    DIST_A = safe_dist(A_laser)

    dataA = {
        "T_amb": T_amb,
        "H_amb": H_amb,
        "T_air": T_airA,
        "H_air": H_airA,
        "T_wat": T_watA,
        "H_wat": H_watA,
        "UV": UV_A,
        "LUX": LUX_A,
        "IR": IR_A,
        "DIST": DIST_A
    }

    # ---------- B ----------
    T_airB, H_airB = safe_sht(B_air)
    T_watB, H_watB = safe_sht(B_wat)
    UV_B = safe_uv(B_uv)
    LUX_B, IR_B = safe_lux(B_lux)
    DIST_B = safe_dist(B_laser)

    dataB = {
        "T_air": T_airB,
        "H_air": H_airB,
        "T_wat": T_watB,
        "H_wat": H_watB,
        "UV": UV_B,
        "LUX": LUX_B,
        "IR": IR_B,
        "DIST": DIST_B
    }

    # ---------- C ----------
    T_airC, H_airC = safe_sht(C_air)
    T_watC, H_watC = safe_sht(C_wat)
    UV_C = safe_uv(C_uv)
    LUX_C, IR_C = safe_lux(C_lux)
    DIST_C = safe_dist(C_laser)

    dataC = {
        "T_air": T_airC,
        "H_air": H_airC,
        "T_wat": T_watC,
        "H_wat": H_watC,
        "UV": UV_C,
        "LUX": LUX_C,
        "IR": IR_C,
        "DIST": DIST_C
    }

    # ---------- D (Wind) ----------
    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4   # معاملك التجريبي
    dataD = {"WIND_m_s": WIND}

    # ---------- PRINT ----------
    print("-" * 70)
    print("A:", dataA)
    print("B:", dataB)
    print("C:", dataC)
    print("D:", dataD)

    # ---------- SEND ----------
    send_ts(API_A, dataA)
    send_ts(API_B, dataB)
    send_ts(API_C, dataC)
    send_ts(API_D, dataD)

    cycle += 1
    if cycle >= 15:   # ~5 دقائق
        print("Auto reset for OTA update...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
