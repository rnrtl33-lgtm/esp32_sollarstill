

import time
import gc
import socket
from machine import SoftI2C, Pin

# ThingSpeak API keys
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# Simple HTTP GET using raw sockets
def http_get(url):
    try:
        _, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]

        s = socket.socket()
        s.connect(addr)
        s.send(
            b"GET /" + path.encode() + b" HTTP/1.0\r\n"
            b"Host: " + host.encode() + b"\r\n\r\n"
        )

        body = b""
        while True:
            part = s.recv(128)
            if not part:
                break
            body += part

        s.close()

        # Strip headers
        if b"\r\n\r\n" in body:
            body = body.split(b"\r\n\r\n", 1)[1]

        return body.decode()

    except Exception as e:
        print("HTTP_ERR:", e)
        return None


# Sensor libraries
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X

# I2C bus mapping
i2c_bus = {
    "A1": SoftI2C(scl=Pin(18), sda=Pin(19)),
    "A2": SoftI2C(scl=Pin(5),  sda=Pin(23)),
    "B1": SoftI2C(scl=Pin(26), sda=Pin(25)),
    "B2": SoftI2C(scl=Pin(14), sda=Pin(27)),
    "C1": SoftI2C(scl=Pin(0),  sda=Pin(32)),
    "C2": SoftI2C(scl=Pin(2),  sda=Pin(15)),
}

# Model autodetection
def detect_model():
    scans = {}
    for name, bus in i2c_bus.items():
        try:
            scans[name] = bus.scan()
        except:
            scans[name] = []

    if 0x53 in scans.get("A1", []):
        return "A", scans

    if 0x53 in scans.get("B1", []):
        return "B", scans

    if 0x53 in scans.get("C1", []):
        return "C", scans

    return "NONE", scans


MODEL, scans = detect_model()
print("Detected model:", MODEL)
print("I2C scan results:", scans)


# Initialization for each model
def init_model_A():
    A1 = i2c_bus["A1"]
    A2 = i2c_bus["A2"]

    return {
        "ambient": SHT30(A1, 0x45),
        "uv":      LTR390(A1, 0x53),
        "laser":   VL53L0X(A1, 0x29),
        "air":     SHT30(A2, 0x45),
        "water":   SHT30(A2, 0x44),
        "lux":     TSL2591(A2, 0x29),
    }

def init_model_B():
    B1 = i2c_bus["B1"]
    B2 = i2c_bus["B2"]

    return {
        "uv":      LTR390(B1, 0x53),
        "laser":   VL53L0X(B1, 0x29),
        "air":     SHT30(B2, 0x45),
        "water":   SHT30(B2, 0x44),
        "lux":     TSL2591(B2, 0x29),
    }

def init_model_C():
    C1 = i2c_bus["C1"]
    C2 = i2c_bus["C2"]

    return {
        "uv":      LTR390(C1, 0x53),
        "laser":   VL53L0X(C1, 0x29),
        "air":     SHT30(C2, 0x45),
        "water":   SHT30(C2, 0x44),
        "lux":     TSL2591(C2, 0x29),
    }


# Wind sensor
wind_pin = Pin(13, Pin.IN)

def read_wind():
    return wind_pin.value()


# Select model
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
    sensors = {}
    API = API_D
    print("No model detected — wind-only mode")


# Read sensors
def read_all():
    out = {}

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

    out["wind"] = read_wind()

    return out


# Upload to ThingSpeak
def send_to_ts(values):
    url = "http://api.thingspeak.com/update?api_key=" + API
    i = 1
    for v in values.values():
        url += "&field{}={}".format(i, v)
        i += 1

    resp = http_get(url)
    print("TS:", resp)


# Main loop
while True:
    gc.collect()
    data = read_all()
    print("DATA:", data)
    send_to_ts(data)
    time.sleep(20)
