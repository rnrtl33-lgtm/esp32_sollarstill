# main.py — unified model reader + TS + auto-restart OTA

import time, gc, socket, urequests
from machine import Pin, SoftI2C, reset

# sensor drivers
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.hx711 import HX711

# TS keys
API_A = "EU6EE36IJWSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"


# --------------------------
# Simple HTTP GET
# --------------------------
def http_get(url):
    try:
        proto, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(b"GET /" + path.encode() + b" HTTP/1.0\r\nHost:" +
               host.encode() + b"\r\n\r\n")
        data = b""
        while True:
            part = s.recv(256)
            if not part:
                break
            data += part
        s.close()
        return data.split(b"\r\n\r\n", 1)[1].decode()
    except:
        return None


# --------------------------
# I2C
# --------------------------
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))

i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# load cells
hxA = HX711(34, 33)
hxB = HX711(35, 33)
hxC = HX711(36, 33)


# --------------------------
# init sensors
# --------------------------
def init_A():
    return {
        "ambient": SHT30(i2cA1, addr=0x45),
        "uv":      LTR390(i2cA1, addr=0x53),
        "laser":   VL53L0X(i2cA1, addr=0x29),
        "air":     SHT30(i2cA2, addr=0x45),
        "water":   SHT30(i2cA2, addr=0x44),
        "lux":     TSL2591(i2cA2, addr=0x29),
        "load":    hxA
    }

def init_B():
    return {
        "uv":      LTR390(i2cB1, addr=0x53),
        "laser":   VL53L0X(i2cB1, addr=0x29),
        "air":     SHT30(i2cB2, addr=0x45),
        "water":   SHT30(i2cB2, addr=0x44),
        "lux":     TSL2591(i2cB2, addr=0x29),
        "load":    hxB
    }

def init_C():
    return {
        "uv":      LTR390(i2cC1, addr=0x53),
        "laser":   VL53L0X(i2cC1, addr=0x29),
        "air":     SHT30(i2cC2, addr=0x45),
        "water":   SHT30(i2cC2, addr=0x44),
        "lux":     TSL2591(i2cC2, addr=0x29),
        "load":    hxC
    }


sA = init_A()
sB = init_B()
sC = init_C()


# --------------------------
# readers (A/B/C/D)
# --------------------------
def read_A():
    t1, h1 = sA["ambient"].measure()
    t2, h2 = sA["air"].measure()
    t3, h3 = sA["water"].measure()
    return {
        "ambient_temp": t1,
        "ambient_hum": h1,
        "uv": sA["uv"].read_uv(),
        "distance": sA["laser"].read(),
        "air_temp": t2,
        "air_hum": h2,
        "water_temp": t3,
        "water_hum": h3,
        "lux": sA["lux"].read_lux(),
        "load": sA["load"].read()
    }

def read_B():
    t2, h2 = sB["air"].measure()
    t3, h3 = sB["water"].measure()
    return {
        "uv": sB["uv"].read_uv(),
        "distance": sB["laser"].read(),
        "air_temp": t2,
        "air_hum": h2,
        "water_temp": t3,
        "water_hum": h3,
        "lux": sB["lux"].read_lux(),
        "load": sB["load"].read()
    }

def read_C():
    t2, h2 = sC["air"].measure()
    t3, h3 = sC["water"].measure()
    return {
        "uv": sC["uv"].read_uv(),
        "distance": sC["laser"].read(),
        "air_temp": t2,
        "air_hum": h2,
        "water_temp": t3,
        "water_hum": h3,
        "lux": sC["lux"].read_lux(),
        "load": sC["load"].read()
    }

def read_D():
    return {"wind": 0}  # no wind sensor now


# --------------------------
# ThingSpeak
# --------------------------
def send_ts(key, data):
    url = "http://api.thingspeak.com/update?api_key=" + key
    i = 1
    for v in data.values():
        url += "&field{}={}".format(i, v); i += 1
    print("TS:", http_get(url))


# --------------------------
# MAIN LOOP
# --------------------------
print("\n>>> Unified Reader Running (Auto-Restart Mode) <<<\n")

cycle = 0

while True:

    A = read_A()
    B = read_B()
    C = read_C()
    D = read_D()

    print("A:", A)
    print("B:", B)
    print("C:", C)
    print("D:", D)

    send_ts(API_A, A)
    send_ts(API_B, B)
    send_ts(API_C, C)
    send_ts(API_D, D)

    cycle += 1
    if cycle >= 15:   # ≈ 5 minutes
        print("Auto-restart for OTA update…")
        time.sleep(1)
        reset()

    time.sleep(20)
 
