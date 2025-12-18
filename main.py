# ======================================================
# main.py — Unified Environmental Monitor (SAFE VERSION)
# Models: A + B + C + D (Wind only)
# Compatible with OTA traditional + auto-reset
# ======================================================

import time
from machine import Pin, SoftI2C

# ----------------------
# SAFE CALL (CRITICAL)
# ----------------------
def safe_call(fn, default=None):
    try:
        return fn()
    except:
        return default

# ----------------------
# Libraries
# ----------------------
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X

# ======================================================
# I2C BUSES
# ======================================================

# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# ======================================================
# SENSOR INIT (NO CRASH)
# ======================================================

def init_if_present(i2c, addr, constructor):
    try:
        if addr in i2c.scan():
            return constructor()
    except:
        pass
    return None

# -------- Model A --------
A_amb   = init_if_present(i2c_A1, 0x45, lambda: SHT30(i2c_A1, addr=0x45))
A_air   = init_if_present(i2c_A2, 0x45, lambda: SHT30(i2c_A2, addr=0x45))
A_wat   = init_if_present(i2c_A2, 0x44, lambda: SHT30(i2c_A2, addr=0x44))
A_uv    = init_if_present(i2c_A1, 0x53, lambda: LTR390(i2c_A1))
A_lux   = init_if_present(i2c_A2, 0x29, lambda: TSL2591(i2c_A2))
A_laser = init_if_present(i2c_A1, 0x29, lambda: VL53L0X(i2c_A1))

# -------- Model B --------
B_air   = init_if_present(i2c_B2, 0x45, lambda: SHT30(i2c_B2, addr=0x45))
B_wat   = init_if_present(i2c_B2, 0x44, lambda: SHT30(i2c_B2, addr=0x44))
B_uv    = init_if_present(i2c_B1, 0x53, lambda: LTR390(i2c_B1))
B_lux   = init_if_present(i2c_B2, 0x29, lambda: TSL2591(i2c_B2))
B_laser = init_if_present(i2c_B1, 0x29, lambda: VL53L0X(i2c_B1))

# -------- Model C --------
C_air   = init_if_present(i2c_C2, 0x45, lambda: SHT30(i2c_C2, addr=0x45))
C_wat   = init_if_present(i2c_C2, 0x44, lambda: SHT30(i2c_C2, addr=0x44))
C_uv    = init_if_present(i2c_C1, 0x53, lambda: LTR390(i2c_C1))
C_lux   = init_if_present(i2c_C2, 0x29, lambda: TSL2591(i2c_C2))
C_laser = init_if_present(i2c_C1, 0x29, lambda: VL53L0X(i2c_C1))

# ======================================================
# WIND SENSOR (Model D)
# ======================================================
wind_pin = Pin(4, Pin.IN)
wind_pulses = 0

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

wind_timer = time.time()
WIND_SPEED = 0.0

# ======================================================
# MAIN LOOP
# ======================================================

print("\n>>> MAIN RUNNING (SAFE MODE: A+B+C+D) <<<\n")

while True:

    # ================= MODEL A =================
    A_Tamb, A_Hamb = safe_call(A_amb.measure, (None, None)) if A_amb else (None, None)
    A_Tair, A_Hair = safe_call(A_air.measure, (None, None)) if A_air else (None, None)
    A_Twat, A_Hwat = safe_call(A_wat.measure, (None, None)) if A_wat else (None, None)

    A_UV = safe_call(A_uv.read_uv) if A_uv else None

    lux_raw = safe_call(A_lux.get_raw_luminosity) if A_lux else None
    A_LUX = A_lux.calculate_lux(*lux_raw) if lux_raw else None

    A_DIST = safe_call(A_laser.read) if A_laser else None

    A = {
        "T_amb": A_Tamb, "H_amb": A_Hamb,
        "T_air": A_Tair, "H_air": A_Hair,
        "T_wat": A_Twat, "H_wat": A_Hwat,
        "LUX": A_LUX, "UV": A_UV, "DIST": A_DIST
    }

    # ================= MODEL B =================
    B_Tair, B_Hair = safe_call(B_air.measure, (None, None)) if B_air else (None, None)
    B_Twat, B_Hwat = safe_call(B_wat.measure, (None, None)) if B_wat else (None, None)

    B_UV = safe_call(B_uv.read_uv) if B_uv else None
    lux_raw = safe_call(B_lux.get_raw_luminosity) if B_lux else None
    B_LUX = B_lux.calculate_lux(*lux_raw) if lux_raw else None
    B_DIST = safe_call(B_laser.read) if B_laser else None

    B = {
        "T_air": B_Tair, "H_air": B_Hair,
        "T_wat": B_Twat, "H_wat": B_Hwat,
        "LUX": B_LUX, "UV": B_UV, "DIST": B_DIST
    }

    # ================= MODEL C =================
    C_Tair, C_Hair = safe_call(C_air.measure, (None, None)) if C_air else (None, None)
    C_Twat, C_Hwat = safe_call(C_wat.measure, (None, None)) if C_wat else (None, None)

    C_UV = safe_call(C_uv.read_uv) if C_uv else None
    lux_raw = safe_call(C_lux.get_raw_luminosity) if C_lux else None
    C_LUX = C_lux.calculate_lux(*lux_raw) if lux_raw else None
    C_DIST = safe_call(C_laser.read) if C_laser else None

    C = {
        "T_air": C_Tair, "H_air": C_Hair,
        "T_wat": C_Twat, "H_wat": C_Hwat,
        "LUX": C_LUX, "UV": C_UV, "DIST": C_DIST
    }

    # ================= WIND =================
    now = time.time()
    if now - wind_timer >= 10:
        WIND_SPEED = round((wind_pulses * 0.4) / 10.0, 2)
        wind_pulses = 0
        wind_timer = now

    D = {"WIND_m_s": WIND_SPEED}

    # ================= OUTPUT =================
    print("-" * 70)
    print("A:", A)
    print("B:", B)
    print("C:", C)
    print("D:", D)

    time.sleep(20)
