# ==================================================
# main.py — Models A+B+C+D
# LTR390 = UV ONLY
# Stable + OTA reset-cycle
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

# ------------------
# Libraries
# ------------------
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X

# ------------------
# ThingSpeak API Keys
# ------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# ------------------
# I2C Buses
# ------------------
# Model A
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# ------------------
# Sensors Init (SAFE)
# ------------------
def safe(init_fn):
    try:
        return init_fn()
    except:
        return None

# A
A_amb   = safe(lambda: SHT30(i2cA1, 0x45))
A_air   = safe(lambda: SHT30(i2cA2, 0x45))
A_wat   = safe(lambda: SHT30(i2cA2, 0x44))
A_uv    = safe(lambda: LTR390(i2cA1))
A_lux   = safe(lambda: TSL2591(i2cA2))
A_laser = safe(lambda: VL53L0X(i2cA1))

# B
B_air   = safe(lambda: SHT30(i2cB2, 0x45))
B_wat   = safe(lambda: SHT30(i2cB2, 0x44))
B_uv    = safe(lambda: LTR390(i2cB1))
B_lux   = safe(lambda: TSL2591(i2cB2))
B_laser = safe(lambda: VL53L0X(i2cB1))

# C
C_air   = safe(lambda: SHT30(i2cC2, 0x45))
C_wat   = safe(lambda: SHT30(i2cC2, 0x44))
C_uv    = safe(lambda: LTR390(i2cC1))
C_lux   = safe(lambda: TSL2591(i2cC2))
C_laser = safe(lambda: VL53L0X(i2cC1))

# ------------------
# Wind Sensor (Model D)
# ------------------
wind_pulses = 0
wind_pin = Pin(4, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ------------------
# ThingSpeak Sender
# ------------------
def send_ts(api, data):
    try:
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        import urequests
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ------------------
# MAIN LOOP
# ------------------
print("\n>>> MAIN RUNNING (ALL SENSORS | UV ONLY) <<<\n")

cycle = 0

while True:

    # ===== Model A =====
    T_amb, H_amb = A_amb.measure() if A_amb else (None, None)
    T_airA, H_airA = A_air.measure() if A_air else (None, None)
    T_watA, H_watA = A_wat.measure() if A_wat else (None, None)

    UV_A = A_uv.read_uv() if A_uv else None

    fullA, IR_A = A_lux.get_raw_luminosity() if A_lux else (None, None)
    LUX_A = A_lux.calculate_lux(fullA, IR_A) if A_lux else None

    try:
        DIST_A = A_laser.read() if A_laser else None
    except:
        DIST_A = None

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

    # ===== Model B =====
    T_airB, H_airB = B_air.measure() if B_air else (None, None)
    T_watB, H_watB = B_wat.measure() if B_wat else (None, None)

    UV_B = B_uv.read_uv() if B_uv else None

    fullB, IR_B = B_lux.get_raw_luminosity() if B_lux else (None, None)
    LUX_B = B_lux.calculate_lux(fullB, IR_B) if B_lux else None

    try:
        DIST_B = B_laser.read() if B_laser else None
    except:
        DIST_B = None

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

    # ===== Model C =====
    T_airC, H_airC = C_air.measure() if C_air else (None, None)
    T_watC, H_watC = C_wat.measure() if C_wat else (None, None)

    UV_C = C_uv.read_uv() if C_uv else None

    fullC, IR_C = C_lux.get_raw_luminosity() if C_lux else (None, None)
    LUX_C = C_lux.calculate_lux(fullC, IR_C) if C_lux else None

    try:
        DIST_C = C_laser.read() if C_laser else None
    except:
        DIST_C = None

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

    # ===== Model D (Wind) =====
    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4   # معاملك التجريبي

    dataD = {"WIND_m_s": WIND}

    # ----- PRINT -----
    print("-" * 70)
    print("A:", dataA)
    print("B:", dataB)
    print("C:", dataC)
    print("D:", dataD)

    # ----- SEND -----
    send_ts(API_A, dataA)
    send_ts(API_B, dataB)
    send_ts(API_C, dataC)
    send_ts(API_D, dataD)

    cycle += 1
    if cycle >= 15:   # ≈ 5 دقائق
        print("Auto reset for OTA update...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
