# ==================================================
# main.py — Unified Models A+B+C+D (NO WEIGHT)
# ENODEV SAFE + ThingSpeak + OTA Live
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

# ==================================================
# SAFE SENSOR INIT (CRITICAL)
# ==================================================
def init_sensor(i2c, addr, ctor):
    try:
        if addr in i2c.scan():
            return ctor()
        else:
            print("Sensor missing:", hex(addr))
    except Exception as e:
        print("Init failed @", hex(addr), e)
    return None

# ==================================================
# I2C Buses (100 kHz)
# ==================================================
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19), freq=100000)
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23), freq=100000)

i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25), freq=100000)
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27), freq=100000)

i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32), freq=100000)
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15), freq=100000)

# ==================================================
# Sensors Init (SAFE)
# ==================================================
# Model A
A_amb   = init_sensor(i2cA1, 0x45, lambda: SHT30(i2cA1, 0x45))
A_air   = init_sensor(i2cA2, 0x45, lambda: SHT30(i2cA2, 0x45))
A_wat   = init_sensor(i2cA2, 0x44, lambda: SHT30(i2cA2, 0x44))
A_uv    = init_sensor(i2cA1, 0x53, lambda: LTR390(i2cA1))
A_lux   = init_sensor(i2cA2, 0x29, lambda: TSL2591(i2cA2))
A_laser = init_sensor(i2cA1, 0x29, lambda: VL53L0X(i2cA1))

# Model B
B_air   = init_sensor(i2cB2, 0x45, lambda: SHT30(i2cB2, 0x45))
B_wat   = init_sensor(i2cB2, 0x44, lambda: SHT30(i2cB2, 0x44))
B_uv    = init_sensor(i2cB1, 0x53, lambda: LTR390(i2cB1))
B_lux   = init_sensor(i2cB2, 0x29, lambda: TSL2591(i2cB2))
B_laser = init_sensor(i2cB1, 0x29, lambda: VL53L0X(i2cB1))

# Model C
C_air   = init_sensor(i2cC2, 0x45, lambda: SHT30(i2cC2, 0x45))
C_wat   = init_sensor(i2cC2, 0x44, lambda: SHT30(i2cC2, 0x44))
C_uv    = init_sensor(i2cC1, 0x53, lambda: LTR390(i2cC1))
C_lux   = init_sensor(i2cC2, 0x29, lambda: TSL2591(i2cC2))
C_laser = init_sensor(i2cC1, 0x29, lambda: VL53L0X(i2cC1))

# ==================================================
# Wind Sensor
# ==================================================
wind_pulses = 0
wind_pin = Pin(4, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ==================================================
# ThingSpeak Sender
# ==================================================
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

# ==================================================
# MAIN LOOP
# ==================================================
print("\n>>> MAIN RUNNING (ENODEV SAFE) <<<\n")

cycle = 0

while True:

    def read_sht(s):
        return s.measure() if s else (None, None)

    # --- A ---
    T_amb, H_amb = read_sht(A_amb)
    T_airA, H_airA = read_sht(A_air)
    T_watA, H_watA = read_sht(A_wat)

    UV_A = A_uv.read_uv() if A_uv else None
    luxA = A_lux.get_raw_luminosity() if A_lux else None
    LUX_A = A_lux.calculate_lux(*luxA) if luxA else None
    DIST_A = A_laser.read() if A_laser else None

    dataA = {
        "T_amb": T_amb, "H_amb": H_amb,
        "T_air": T_airA, "H_air": H_airA,
        "T_wat": T_watA, "H_wat": H_watA,
        "UV": UV_A, "LUX": LUX_A, "DIST": DIST_A
    }

    # --- B ---
    T_airB, H_airB = read_sht(B_air)
    T_watB, H_watB = read_sht(B_wat)
    UV_B = B_uv.read_uv() if B_uv else None
    luxB = B_lux.get_raw_luminosity() if B_lux else None
    LUX_B = B_lux.calculate_lux(*luxB) if luxB else None
    DIST_B = B_laser.read() if B_laser else None

    dataB = {
        "T_air": T_airB, "H_air": H_airB,
        "T_wat": T_watB, "H_wat": H_watB,
        "UV": UV_B, "LUX": LUX_B, "DIST": DIST_B
    }

    # --- C ---
    T_airC, H_airC = read_sht(C_air)
    T_watC, H_watC = read_sht(C_wat)
    UV_C = C_uv.read_uv() if C_uv else None
    luxC = C_lux.get_raw_luminosity() if C_lux else None
    LUX_C = C_lux.calculate_lux(*luxC) if luxC else None
    DIST_C = C_laser.read() if C_laser else None

    dataC = {
        "T_air": T_airC, "H_air": H_airC,
        "T_wat": T_watC, "H_wat": H_watC,
        "UV": UV_C, "LUX": LUX_C, "DIST": DIST_C
    }

    pulses = wind_pulses
    wind_pulses = 0
    dataD = {"WIND_m_s": pulses * 0.4}

    print("-"*70)
    print("A:", dataA)
    print("B:", dataB)
    print("C:", dataC)
    print("D:", dataD)

    send_ts(API_A, dataA)
    send_ts(API_B, dataB)
    send_ts(API_C, dataC)
    send_ts(API_D, dataD)

    cycle += 1
    if cycle >= 15:
        print("Auto reset for OTA update...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
