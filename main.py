

import time, gc, socket, urequests
from machine import Pin, SoftI2C

# sensor drivers
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.hx711 import HX711
from lib.wind import WindSensor

# ThingSpeak keys
API_A = "EU6EE36IJWSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# OTA / Kill URLs
RAW_MAIN = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"
RAW_KILL = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/kill.txt"


# -------------------------------------------------
# Simple HTTP GET
# -------------------------------------------------
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


# -------------------------------------------------
# Kill Switch
# -------------------------------------------------
def check_kill():
    try:
        r = urequests.get(RAW_KILL)
        flag = r.text.strip().upper()
        r.close()
        return flag == "STOP"
    except:
        return False


# -------------------------------------------------
# OTA Live (فقط مقارنة واستبدال الملف)
# -------------------------------------------------
def check_ota():
    try:
        r = urequests.get(RAW_MAIN)
        new_code = r.text
        r.close()

        with open("main.py") as f:
            old_code = f.read()

        if new_code.strip() != old_code.strip():
            print("\n>>> OTA: New version detected, applying update...\n")
            with open("main.py", "w") as f:
                f.write(new_code)

            time.sleep(1)
            exec(new_code, {})      # تشغيل النسخة الجديدة مباشرة
            return True

    except Exception as e:
        print("OTA error:", e)

    return False


# -------------------------------------------------
# I2C buses for A/B/C
# -------------------------------------------------
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))

i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))


# Wind / weight sensors
wind = WindSensor(13)
hxA  = HX711(34, 33)
hxB  = HX711(35, 33)
hxC  = HX711(36, 33)


# -------------------------------------------------
# Init sensors for each model
# -------------------------------------------------
def init_A():
    return {
        "ambient":  SHT30(i2cA1, addr=0x45),
        "uv":       LTR390(i2cA1, addr=0x53),
        "laser":    VL53L0X(i2cA1, addr=0x29),
        "air":      SHT30(i2cA2, addr=0x45),
        "water":    SHT30(i2cA2, addr=0x44),
        "lux":      TSL2591(i2cA2, addr=0x29),
        "load":     hxA
    }

def init_B():
    return {
        "uv":       LTR390(i2cB1, addr=0x53),
        "laser":    VL53L0X(i2cB1, addr=0x29),
        "air":      SHT30(i2cB2, addr=0x45),
        "water":    SHT30(i2cB2, addr=0x44),
        "lux":      TSL2591(i2cB2, addr=0x29),
        "load":     hxB
    }

def init_C():
    return {
        "uv":       LTR390(i2cC1, addr=0x53),
        "laser":    VL53L0X(i2cC1, addr=0x29),
        "air":      SHT30(i2cC2, addr=0x45),
        "water":    SHT30(i2cC2, addr=0x44),
        "lux":      TSL2591(i2cC2, addr=0x29),
        "load":     hxC
    }


sA = init_A()
sB = init_B()
sC = init_C()


# -------------------------------------------------
# Read each model
# -------------------------------------------------
def read_A():
    out = {}
    t, h = sA["ambient"].measure()
    out["ambient_temp"] = t
    out["ambient_hum"]  = h

    out["uv"]       = sA["uv"].read_uv()
    out["distance"] = sA["laser"].read()

    t, h = sA["air"].measure()
    out["air_temp"] = t
    out["air_hum"]  = h

    t, h = sA["water"].measure()
    out["water_temp"] = t
    out["water_hum"]  = h

    out["lux"]   = sA["lux"].read_lux()
    out["load"]  = sA["load"].read()
    out["wind"]  = wind.read()

    return out


def read_B():
    out = {}
    out["uv"]       = sB["uv"].read_uv()
    out["distance"] = sB["laser"].read()

    t, h = sB["air"].measure()
    out["air_temp"] = t
    out["air_hum"]  = h

    t, h = sB["water"].measure()
    out["water_temp"] = t
    out["water_hum"]  = h

    out["lux"]  = sB["lux"].read_lux()
    out["load"] = sB["load"].read()
    out["wind"] = wind.read()

    return out


def read_C():
    out = {}
    out["uv"]       = sC["uv"].read_uv()
    out["distance"] = sC["laser"].read()

    t, h = sC["air"].measure()
    out["air_temp"] = t
    out["air_hum"]  = h

    t, h = sC["water"].measure()
    out["water_temp"] = t
    out["water_hum"]  = h

    out["lux"]  = sC["lux"].read_lux()
    out["load"] = sC["load"].read()
    out["wind"] = wind.read()

    return out


# Model D (wind only)
def read_D():
    return {"wind": wind.read()}


# -------------------------------------------------
# ThingSpeak
# -------------------------------------------------
def send_ts(api_key, data):
    url = "http://api.thingspeak.com/update?api_key=" + api_key
    i = 1
    for v in data.values():
        url += "&field{}={}".format(i, v)
        i += 1
    print("TS:", http_get(url))


# =====================================================
#                         LOOP
# =====================================================
print("\n>>> Unified Reader Is Running <<<\n")

while True:

    if check_kill():
        print("\nSTOP signal received — halting system.\n")
        break

    if check_ota():
        break

    A = read_A()
    B = read_B()
    C = read_C()
    D = read_D()

    print("\nA:", A)
    print("B:", B)
    print("C:", C)
    print("D:", D)

    send_ts(API_A, A)
    send_ts(API_B, B)
    send_ts(API_C, C)
    send_ts(API_D, D)

    print("Sleeping 20 seconds...\n")
    time.sleep(20)
