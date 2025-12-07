import time, network, urequests
from machine import I2C, Pin
from lib.sht30 import SHT30
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X

print("MAIN STARTED")

# -----------------------------
# WiFi
# -----------------------------
SSID = "HUAWEI-1006VE_Wi-Fi5"
PASS = "FPdGG9N7"

def ensure_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASS)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    print("WiFi:", wlan.ifconfig())
    return wlan


# -----------------------------
# ThingSpeak Keys
# -----------------------------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"


def ts_send(api, f1, f2, f3, f4):
    try:
        url = (
            "https://api.thingspeak.com/update?"
            "api_key={}&field1={}&field2={}&field3={}&field4={}"
        ).format(api, f1, f2, f3, f4)
        r = urequests.get(url)
        print("TS:", api, "->", r.text)
        r.close()
    except Exception as e:
        print("TS ERROR:", api, e)


# -----------------------------
# I2C Buses (6 buses)
# -----------------------------
print("Init I2C buses...")

# استخدمنا 0 و 1 للهاردوير
i2c_A1 = I2C(0, scl=Pin(18), sda=Pin(19))
i2c_A2 = I2C(1, scl=Pin(5),  sda=Pin(23))

# البقية Software I2C باستخدام -1
i2c_B1 = I2C(-1, scl=Pin(26), sda=Pin(25))
i2c_B2 = I2C(-1, scl=Pin(14), sda=Pin(27))

i2c_C1 = I2C(-1, scl=Pin(0),  sda=Pin(32))
i2c_C2 = I2C(-1, scl=Pin(2),  sda=Pin(15))


# -----------------------------
# XSHUT pins for VL53
# -----------------------------
XSHUT_A = Pin(17, Pin.OUT)
XSHUT_B = Pin(22, Pin.OUT)
XSHUT_C = Pin(4,  Pin.OUT)

def enable_vl53(pin):
    pin.value(1)
    time.sleep_ms(5)


# -----------------------------
# Init Sensors
# -----------------------------
print("Init sensors...")

# نموذج A
enable_vl53(XSHUT_A)
vl53_A = VL53L0X(i2c_A1)
shtA1   = SHT30(i2c_A1)

shtA2_air = SHT30(i2c_A2, addr=0x45)
shtA2_w2  = SHT30(i2c_A2, addr=0x44)
tslA      = TSL2591(i2c_A2)

# نموذج B
enable_vl53(XSHUT_B)
vl53_B = VL53L0X(i2c_B1)

shtB_air = SHT30(i2c_B2, addr=0x45)
shtB_w2  = SHT30(i2c_B2, addr=0x44)
tslB     = TSL2591(i2c_B2)

# نموذج C
enable_vl53(XSHUT_C)
vl53_C = VL53L0X(i2c_C1)

shtC_air = SHT30(i2c_C2, addr=0x45)
shtC_w2  = SHT30(i2c_C2, addr=0x44)
tslC     = TSL2591(i2c_C2)

# حساس الرياح
wind_pin = Pin(13, Pin.IN)

print("All sensors initialized.")


# -----------------------------
# Read Functions
# -----------------------------
def read_model_A():
    t1, h1 = shtA1.measure()
    t2, h2 = shtA2_air.measure()
    t3, h3 = shtA2_w2.measure()
    lux = tslA.lux()
    dist = vl53_A.read()
    print("A:", t1, h1, t2, h2, t3, h3, lux, dist)
    return t1, h1, lux, dist


def read_model_B():
    t1, h1 = shtB_air.measure()
    t2, h2 = shtB_w2.measure()
    lux = tslB.lux()
    dist = vl53_B.read()
    print("B:", t1, h1, lux, dist)
    return t1, h1, lux, dist


def read_model_C():
    t1, h1 = shtC_air.measure()
    t2, h2 = shtC_w2.measure()
    lux = tslC.lux()
    dist = vl53_C.read()
    print("C:", t1, h1, lux, dist)
    return t1, h1, lux, dist


def read_wind():
    w = wind_pin.value()
    print("Wind:", w)
    return w


# -----------------------------
# MAIN LOOP
# -----------------------------
ensure_wifi()
print("System Ready. Entering loop...")

while True:
    try:
        A = read_model_A()
        B = read_model_B()
        C = read_model_C()
        W = read_wind()

        ts_send(API_A, A[0], A[1], A[2], A[3])
        ts_send(API_B, B[0], B[1], B[2], B[3])
        ts_send(API_C, C[0], C[1], C[2], C[3])
        ts_send(API_W, W, 0, 0, 0)

    except Exception as e:
        print("MAIN LOOP ERROR:", e)

    time.sleep(15)


