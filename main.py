# main.py — unified reader for Models A, B, C, D + OTA Live + Kill Switch

import time, gc, socket, urequests
from machine import Pin, SoftI2C

# sensor drivers
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X
from lib.hx711 import HX711
from lib.wind import WindSensor

# ThingSpeak API keys
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

# OTA URLs
RAW_MAIN = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"
RAW_KILL = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/kill.txt"


# -------------- Helper: HTTP GET --------------
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

        body = data.split(b"\r\n\r\n", 1)[1]
        return body.decode()
    except:
        return None


# -------------- Kill Switch --------------
def check_kill():
    try:
        r = urequests.get(RAW_KILL)
        flag = r.text.strip()
        r.close()
        return flag.upper() == "STOP"
    except:
        return False


# -------------- OTA Live --------------
def check_ota():
    try:
        r = urequests.get(RAW_MAIN)
        new = r.text
        r.close()

        with open("main.py") as f:
            old = f.read()

        if new.strip() != old.strip():
            with open("main.py", "w") as f:
                f.write(new)
            print("OTA: New version received → applying update...")
            time.sleep(1)
            exec(new, globals())   # reboot into new version
            return True

    except:
        pass

    return False


# -------------- Sensors Mapping --------------
i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))
i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))
i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

# wind + load cell
wind = WindSensor(13)
hxA  = HX711(34, 33)
hxB  = HX711(35, 33)
hxC  = HX711(36, 33)


# -------------- Initialize Each Model --------------
def init_model_A():
    return {
        "ambient":  SHT30(i2cA1, addr=0x45),
        "uv":       LTR390(i2cA1, addr=0x53),
        "laser":    VL53L0X(i2cA1, addr=0x29),
        "air":      SHT30(i2cA2, addr=0x45),
        "water":    SHT30(i2cA2, addr=0x44),
        "lux":      TSL2591(i2cA2, addr=0x29),
        "ir":       TSL2591(i2cA2, addr=0x29),
        "load":     hxA
    }

def init_model_B():
    return {
        "uv":       LTR390(i2cB1, addr=0x53),
        "laser":    VL53L0X(i2cB1, addr=0x29),
        "air":      SHT30(i2cB2, addr=0x45),
        "water":    SHT30(i2cB2, addr=0x44),
        "lux":      TSL2591(i2cB2, addr=0x29),
        "ir":       TSL2591(i2cB2, addr=0x29),
        "load":     hxB
    }

def init_model_C():
    return {
        "uv":       LTR390(i2cC1, addr=0x53),
        "laser":    VL53L0X(i2cC1, addr=0x29),
        "air":      SHT30(i2cC2, addr=0x45),
        "water":    SHT30(i2cC2, addr=0x44),
        "lux":      TSL2591(i2cC2, addr=0x29),
        "ir":       TSL2591(i2cC2, addr=0x29),
        "load":     hxC
    }


sA = init_model_A()
sB = init_model_B()
sC = init_model_C()


# -------------- Reading Functions --------------
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

    out["lux"]  = sA["lux"].read_lux()
    out["ir"]   = sA["ir"].read_ir()
    out["load"] = sA["load"].read()

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

    out["load"] = sB["load"].read()
    out["lux"]  = sB["lux"].read_lux()
    out["ir"]   = sB["ir"].read_ir()

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

    out["load"] = sC["load"].read()
    out["lux"]  = sC["lux"].read_lux()
    out["ir"]   = sC["ir"].read_ir()

    return out


def read_D():
    return {"wind_speed": wind.read()}


# -------------- Send to ThingSpeak --------------
def send_ts(api, data):
    url = "http://api.thingspeak.com/update?api_key=" + api
    i = 1
    for v in data.values():
        url += "&field{}={}".format(i, v)
        i += 1
    print("TS →", http_get(url))


# =====================================================
#                     MAIN LOOP
# =====================================================

print("\n>>> Unified A+B+C+D Reader Running <<<\n")

MAIN_CODE = open("main.py").read()

while True:

    # Kill switch
    if check_kill():
        print("Kill switch triggered — stopping.")
        break

    # OTA Live
    if check_ota():
        break

    # Read each model
    A = read_A()
    B = read_B()
    C = read_C()
    D = read_D()

    print("A:", A)
    print("B:", B)
    print("C:", C)
    print("D:", D)

    # Send to TS
    send_ts(API_A, A)
    send_ts(API_B, B)
    send_ts(API_C, C)
    send_ts(API_D, D)

    print("Sleeping 20s...\n")
    time.sleep(20)
 
