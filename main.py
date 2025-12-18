

import time, gc
from machine import Pin, SoftI2C, reset

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
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))

i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# ------------------
# Sensors Init
# ------------------
A_amb   = SHT30(i2cA1, 0x45)
A_air   = SHT30(i2cA2, 0x45)
A_wat   = SHT30(i2cA2, 0x44)
A_uv    = LTR390(i2cA1)
A_lux   = TSL2591(i2cA2)
A_laser = VL53L0X(i2cA1)

B_air   = SHT30(i2cB2, 0x45)
B_wat   = SHT30(i2cB2, 0x44)
B_uv    = LTR390(i2cB1)
B_lux   = TSL2591(i2cB2)
B_laser = VL53L0X(i2cB1)

C_air   = SHT30(i2cC2, 0x45)
C_wat   = SHT30(i2cC2, 0x44)
C_uv    = LTR390(i2cC1)
C_lux   = TSL2591(i2cC2)
C_laser = VL53L0X(i2cC1)

# ------------------
# Wind Sensor
# ------------------
wind_pulses = 0
wind_pin = Pin(4, Pin.IN)

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

# ------------------
# Safe Readers
# ------------------
def read_sht(sensor):
    try:
        t, h = sensor.measure()
        if -40 < t < 85 and 0 <= h <= 100:
            return t, h
    except:
        pass
    return None, None

def read_uv(sensor):
    try:
        sensor.set_uv_mode()
        sensor.set_gain(3)
        sensor.set_integration(400)
        time.sleep_ms(500)
        return sensor.read_uv()
    except:
        return None

def read_lux(sensor):
    try:
        time.sleep_ms(400)
        full, ir = sensor.get_raw_luminosity()
        lux = sensor.calculate_lux(full, ir)
        return lux, ir
    except:
        return None, None

def read_dist(sensor):
    try:
        return sensor.read()
    except:
        return None

# ------------------
# ThingSpeak
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
    except:
        pass

# ------------------
# MAIN LOOP
# ------------------
print("\n>>> MAIN RUNNING (TIMING SAFE) <<<\n")

cycle = 0

while True:

    # ===== A =====
    T_amb, H_amb = read_sht(A_amb)
    time.sleep_ms(100)

    T_airA, H_airA = read_sht(A_air)
    time.sleep_ms(100)

    T_watA, H_watA = read_sht(A_wat)
    time.sleep_ms(150)

    UV_A = read_uv(A_uv)
    LUX_A, IR_A = read_lux(A_lux)
    DIST_A = read_dist(A_laser)

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

    # ===== B =====
    T_airB, H_airB = read_sht(B_air)
    time.sleep_ms(100)

    T_watB, H_watB = read_sht(B_wat)
    time.sleep_ms(150)

    UV_B = read_uv(B_uv)
    LUX_B, IR_B = read_lux(B_lux)
    DIST_B = read_dist(B_laser)

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

    # ===== C =====
    T_airC, H_airC = read_sht(C_air)
    time.sleep_ms(100)

    T_watC, H_watC = read_sht(C_wat)
    time.sleep_ms(150)

    UV_C = read_uv(C_uv)
    LUX_C, IR_C = read_lux(C_lux)
    DIST_C = read_dist(C_laser)

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

    # ===== D =====
    pulses = wind_pulses
    wind_pulses = 0
    WIND = pulses * 0.4

    dataD = {"WIND_m_s": WIND}

    print("-" * 70)
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
        print("Auto reset for OTA...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
