# ================================
#   MAIN AUTO-DETECT SYSTEM v4
#   Models A / B / C / D (Wind)
#   Interval = 20 seconds
#   Author: ChatGPT — For Abdullah
# ================================

print("MAIN STARTED — Auto Detect Models A/B/C/D")

import time, gc
from machine import Pin, SoftI2C
import socket


# ==== ThingSpeak API Keys ====
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"


# ========= Lightweight HTTP GET (No ENOMEM) ==========
def http_get(url):
    try:
        proto, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(b"GET /" + path.encode() + b" HTTP/1.0\r\nHost: " +
               host.encode() + b"\r\n\r\n")

        data = b""
        while True:
            chunk = s.recv(128)
            if not chunk:
                break
            data += chunk
        s.close()

        # strip headers
        return data.split(b"\r\n\r\n", 1)[1].decode()

    except Exception as e:
        print("HTTP_ERR:", e)
        return None


# ========== Sensor Libraries ==========
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53 import VL53L0X


# ========== I2C Bus Map ==========
i2c_map = {
    "A1": SoftI2C(scl=Pin(18), sda=Pin(19)),
    "A2": SoftI2C(scl=Pin(5),  sda=Pin(23)),
    "B1": SoftI2C(scl=Pin(26), sda=Pin(25)),
    "B2": SoftI2C(scl=Pin(14), sda=Pin(27)),
    "C1": SoftI2C(scl=Pin(0),  sda=Pin(32)),
    "C2": SoftI2C(scl=Pin(2),  sda=Pin(15)),
}


# ========== Detect Model ==========
def detect_model():
    scans = {k: i2c.scan() for k, i2c in i2c_map.items()}

    if scans["A1"] == [0x29, 0x45, 0x53] or 0x53 in scans["A1"]:
        return "A", scans
    if scans["B1"] == [0x29, 0x53] or 0x53 in scans["B1"]:
        return "B", scans
    if scans["C1"] == [0x29, 0x53] or 0x53 in scans["C1"]:
        return "C", scans

    return "NONE", scans


MODEL, all_scans = detect_model()
print("Detected Model:", MODEL)
print("I2C Scans:", all_scans)


# ========== Initialize Model Sensors ==========
def init_model_A():
    print("INIT Model A")
    A1 = i2c_map["A1"]
    A2 = i2c_map["A2"]

    return {
        "ambient": SHT30(A1, addr=0x45),
        "uv":      LTR390(A1, addr=0x53),
        "laser":   VL53L0X(A1, addr=0x29),
        "air":     SHT30(A2, addr=0x45),
        "water":   SHT30(A2, addr=0x44),
        "lux":     TSL2591(A2, addr=0x29),
    }


def init_model_B():
    print("INIT Model B")
    B1 = i2c_map["B1"]
    B2 = i2c_map["B2"]

    return {
        "uv":      LTR390(B1, addr=0x53),
        "laser":   VL53L0X(B1, addr=0x29),
        "air":     SHT30(B2, addr=0x45),
        "water":   SHT30(B2, addr=0x44),
        "lux":     TSL2591(B2, addr=0x29),
    }


def init_model_C():
    print("INIT Model C")
    C1 = i2c_map["C1"]
    C2 = i2c_map["C2"]

    return {
        "uv":      LTR390(C1, addr=0x53),
        "laser":   VL53L0X(C1, addr=0x29),
        "air":     SHT30(C2, addr=0x45),
        "water":   SHT30(C2, addr=0x44),
        "lux":     TSL2591(C2, addr=0x29),
    }


# ========== Wind Sensor Model D ==========
wind_pin = Pin(13, Pin.IN)

def read_wind():
    # Simple frequency counter placeholder
    return wind_pin.value()


# =====================
#  BUILD SENSOR OBJECTS
# =====================

if MODEL == "A":
    sensors = init_model_A()
    API = API_A

elif MODEL == "B":
    sensors = init_model_B()
    API = API_B

elif MODEL == "C":
    sensors = init_model_C()
    API = API_C

else:
    print("NO MODEL DETECTED — Running WIND ONLY MODE")
    sensors = {}
    API = API_D



# ========== READ MODEL VALUES ==========
def read_all():
    out = {}

    try:
        if "ambient" in sensors:
            t, h = sensors["ambient"].measure()
            out["ambient_temp"] = t
            out["ambient_hum"] = h

        if "air" in sensors:
            t, h = sensors["air"].measure()
            out["air_temp"] = t
            out["air_hum"] = h

        if "water" in sensors:
            t, h = sensors["water"].measure()
            out["water_temp"] = t
            out["water_hum"] = h

        if "uv" in sensors:
            out["uv"] = sensors["uv"].read_uv()

        if "lux" in sensors:
            out["lux"] = sensors["lux"].read_lux()

        if "laser" in sensors:
            out["distance"] = sensors["laser"].read()

    except Exception as e:
        print("READ_ERR:", e)

    # Add wind model
    out["wind"] = read_wind()

    return out


# ========== SEND TO THINGSPEAK ==========
def send_to_ts(data):
    base = "http://api.thingspeak.com/update?api_key=" + API

    i = 1
    for v in data.values():
        base += "&field{}={}".format(i, v)
        i += 1

    resp = http_get(base)
    print("TS:", resp)


# ========== MAIN LOOP ==========
while True:
    gc.collect()
    values = read_all()
    print("DATA:", values)

    send_to_ts(values)
    print("Sleeping 20 seconds...\n")

    time.sleep(20)
