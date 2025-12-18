# ==================================================
# main.py — LTR390 UV ONLY (ENODEV SAFE)
# Compatible with OTA reset-cycle
# ==================================================

import time, gc
from machine import Pin, SoftI2C, reset

from lib.ltr390_fixed import LTR390

# ------------------
# ThingSpeak
# ------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"

# ------------------
# I2C buses
# ------------------
i2cA = SoftI2C(scl=Pin(18), sda=Pin(19), freq=100000)
i2cB = SoftI2C(scl=Pin(26), sda=Pin(25), freq=100000)
i2cC = SoftI2C(scl=Pin(0),  sda=Pin(32), freq=100000)

# ------------------
# Safe UV reader
# ------------------
def read_uv(i2c, label):
    try:
        if 0x53 not in i2c.scan():
            print(label, "LTR390 not found")
            return None

        sensor = LTR390(i2c)
        time.sleep_ms(50)
        uv = sensor.read_uv()
        return uv

    except Exception as e:
        print(label, "UV error:", e)
        return None

# ------------------
# ThingSpeak sender
# ------------------
def send_ts(api, value):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key={}&field1={}".format(api, value)
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

# ==================================================
# MAIN LOOP
# ==================================================
print("\n>>> LTR390 UV MODE (SAFE) <<<\n")

cycle = 0

while True:

    UV_A = read_uv(i2cA, "A")
    UV_B = read_uv(i2cB, "B")
    UV_C = read_uv(i2cC, "C")

    print("-" * 40)
    print("A UV:", UV_A)
    print("B UV:", UV_B)
    print("C UV:", UV_C)

    if UV_A is not None:
        send_ts(API_A, UV_A)
    if UV_B is not None:
        send_ts(API_B, UV_B)
    if UV_C is not None:
        send_ts(API_C, UV_C)

    cycle += 1
    if cycle >= 15:   # ~5 minutes
        print("Auto reset for OTA update")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
