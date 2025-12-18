# ==============================
# MAIN.py — Unified Models A+B+C+D
# Weight sensor REMOVED
# ==============================

import time
from machine import Pin, SoftI2C

# ---- Libraries ----
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X

# ==============================
# I2C BUSES
# ==============================

# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# ==============================
# SENSORS INIT
# ==============================

# ---- Model A ----
A_amb = SHT30(i2c_A1, addr=0x45)
A_air = SHT30(i2c_A2, addr=0x45)
A_wat = SHT30(i2c_A2, addr=0x44)
A_uv  = LTR390(i2c_A1)
A_lux = TSL2591(i2c_A2)
A_laser = VL53L0X(i2c_A1)

# ---- Model B ----
B_air = SHT30(i2c_B2, addr=0x45)
B_wat = SHT30(i2c_B2, addr=0x44)
B_uv  = LTR390(i2c_B1)
B_lux = TSL2591(i2c_B2)
B_laser = VL53L0X(i2c_B1)

# ---- Model C ----
C_air = SHT30(i2c_C2, addr=0x45)
C_wat = SHT30(i2c_C2, addr=0x44)
C_uv  = LTR390(i2c_C1)
C_lux = TSL2591(i2c_C2)
C_laser = VL53L0X(i2c_C1)

# ==============================
# WIND SENSOR (Model D)
# ==============================

wind_pin = Pin(4, Pin.IN)
wind_pulses = 0

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

wind_timer = time.time()
WIND_SPEED = 0.0

# ==============================
# MAIN LOOP
# ==============================

print("\n>>> MAIN RUNNING (A + B + C + D) <<<\n")

while True:

    # ---------- MODEL A ----------
    T_amb, H_amb = A_amb.measure()
    T_air, H_air = A_air.measure()
    T_wat, H_wat = A_wat.measure()

    A_UV = A_uv.read_uv()
    full, ir = A_lux.get_raw_luminosity()
    A_LUX = A_lux.calculate_lux(full, ir)

    try:
        A_DIST = A_laser.read()
    except:
        A_DIST = None

    A = {
        "T_amb": round(T_amb, 2),
        "H_amb": round(H_amb, 2),
        "T_air": round(T_air, 2),
        "H_air": round(H_air, 2),
        "T_wat": round(T_wat, 2),
        "H_wat": round(H_wat, 2),
        "LUX": round(A_LUX, 2),
        "UV": A_UV,
        "DIST": A_DIST
    }

    # ---------- MODEL B ----------
    T_air, H_air = B_air.measure()
    T_wat, H_wat = B_wat.measure()

    B_UV = B_uv.read_uv()
    full, ir = B_lux.get_raw_luminosity()
    B_LUX = B_lux.calculate_lux(full, ir)

    try:
        B_DIST = B_laser.read()
    except:
        B_DIST = None

    B = {
        "T_air": round(T_air, 2),
        "H_air": round(H_air, 2),
        "T_wat": round(T_wat, 2),
        "H_wat": round(H_wat, 2),
        "LUX": round(B_LUX, 2),
        "UV": B_UV,
        "DIST": B_DIST
    }

    # ---------- MODEL C ----------
    T_air, H_air = C_air.measure()
    T_wat, H_wat = C_wat.measure()

    C_UV = C_uv.read_uv()
    full, ir = C_lux.get_raw_luminosity()
    C_LUX = C_lux.calculate_lux(full, ir)

    try:
        C_DIST = C_laser.read()
    except:
        C_DIST = None

    C = {
        "T_air": round(T_air, 2),
        "H_air": round(H_air, 2),
        "T_wat": round(T_wat, 2),
        "H_wat": round(H_wat, 2),
        "LUX": round(C_LUX, 2),
        "UV": C_UV,
        "DIST": C_DIST
    }

    # ---------- WIND ----------
    now = time.time()
    if now - wind_timer >= 10:
        WIND_SPEED = round((wind_pulses * 0.4) / 10.0, 2)
        wind_pulses = 0
        wind_timer = now

    D = {"WIND_m_s": WIND_SPEED}

    # ---------- OUTPUT ----------
    print("-" * 70)
    print("A:", A)
    print("B:", B)
    print("C:", C)
    print("D:", D)

    time.sleep(20)
