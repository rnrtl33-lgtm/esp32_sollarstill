# =====================================================
# main.py — Unified Models A + B + C
# Restart-based OTA (boot.py fetches from GitHub)
# =====================================================

import time
import gc
import socket
from machine import Pin, SoftI2C, reset

# =====================================================
# ThingSpeak API KEYS
# =====================================================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"

# =====================================================
# Simple HTTP GET (stable)
# =====================================================
def http_get(url):
    try:
        proto, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        s.send(
            b"GET /" + path.encode() +
            b" HTTP/1.0\r\nHost:" +
            host.encode() + b"\r\n\r\n"
        )
        data = b""
        while True:
            part = s.recv(256)
            if not part:
                break
            data += part
        s.close()
        return data
    except:
        return None

# =====================================================
# I2C BUSES
# =====================================================
# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# =====================================================
# SENSOR LIBRARIES (clean)
# =====================================================
from ltr390_clean import LTR390
from tsl2591_clean import TSL2591

ltr_A = LTR390(i2c_A1)
ltr_B = LTR390(i2c_B1)
ltr_C = LTR390(i2c_C1)

tsl_A = TSL2591(i2c_A2)
tsl_B = TSL2591(i2c_B2)
tsl_C = TSL2591(i2c_C2)

for tsl in (tsl_A, tsl_B, tsl_C):
    tsl.gain = tsl.GAIN_MED
    tsl.integration_time = tsl.INTEGRATIONTIME_300MS

# =====================================================
# HELPERS
# =====================================================
ADDR_TOF = 0x29

def read_distance(i2c):
    try:
        i2c.writeto_mem(ADDR_TOF, 0x00, b"\x01")
        time.sleep_ms(60)
        data = i2c.readfrom_mem(ADDR_TOF, 0x14, 12)
        d = (data[10] << 8) | data[11]
        return d if d < 8190 else None
    except:
        return None

def read_sht30(i2c, addr):
    try:
        i2c.writeto(addr, b"\x2C\x06")
        time.sleep_ms(20)
        data = i2c.readfrom(addr, 6)
        t = -45 + (175 * ((data[0] << 8) | data[1]) / 65535)
        h = 100 * (((data[3] << 8) | data[4]) / 65535)
        return round(t, 2), round(h, 2)
    except:
        return None, None

def read_ltr(ltr):
    try:
        ltr.set_als_mode()
        als = ltr.read_als()
        ltr.set_uvs_mode()
        uv = ltr.read_uv()
        return als, uv
    except:
        return None, None

def read_tsl(tsl):
    try:
        full, ir = tsl.get_raw_luminosity()
        lux = tsl.calculate_lux(full, ir)
        return round(lux, 2), ir
    except:
        return None, None

# =====================================================
# READERS
# =====================================================
def read_A():
    t_amb, _ = read_sht30(i2c_A1, 0x45)
    t_air, _ = read_sht30(i2c_A2, 0x44)
    t_wat, _ = read_sht30(i2c_A2, 0x45)
    als, uv = read_ltr(ltr_A)
    lux, ir = read_tsl(tsl_A)

    return {
        "t_amb": t_amb,
        "t_air": t_air,
        "t_wat": t_wat,
        "uv": uv,
        "dist": read_distance(i2c_A1),
        "lux": lux,
        "ir": ir
    }

def read_B():
    t_air, _ = read_sht30(i2c_B2, 0x44)
    t_wat, _ = read_sht30(i2c_B2, 0x45)
    _, uv = read_ltr(ltr_B)
    lux, ir = read_tsl(tsl_B)

    return {
        "uv": uv,
        "dist": read_distance(i2c_B1),
        "t_air": t_air,
        "t_wat": t_wat,
        "lux": lux,
        "ir": ir
    }

def read_C():
    t_air, _ = read_sht30(i2c_C2, 0x44)
    t_wat, _ = read_sht30(i2c_C2, 0x45)
    _, uv = read_ltr(ltr_C)
    lux, ir = read_tsl(tsl_C)

    return {
        "uv": uv,
        "dist": read_distance(i2c_C1),
        "t_air": t_air,
        "t_wat": t_wat,
        "lux": lux,
        "ir": ir
    }

# =====================================================
# ThingSpeak sender
# =====================================================
def send_ts(key, data):
    url = "http://api.thingspeak.com/update?api_key=" + key
    i = 1
    for v in data.values():
        url += "&field{}={}".format(i, v)
        i += 1
    http_get(url)

# =====================================================
# MAIN LOOP
# =====================================================
print("\n>>> MAIN RUNNING (A+B+C, restart-based OTA) <<<\n")

start_time = time.time()

while True:
    A = read_A()
    B = read_B()
    C = read_C()

    print("A:", A)
    print("B:", B)
    print("C:", C)

    send_ts(API_A, A)
    send_ts(API_B, B)
    send_ts(API_C, C)

    gc.collect()

    # restart after ~5 minutes
    if time.time() - start_time >= 300:
        print("Restarting to allow OTA update...")
        time.sleep(1)
        reset()

    time.sleep(20)
 
