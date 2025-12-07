import time
import network
import urequests
from machine import I2C, SoftI2C, Pin

# ===============================
# WiFi
# ===============================

SSID = "Abdullah's phone"
PASS = "42012999"

def wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASS)
        t = 20
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    print("WiFi:", wlan.ifconfig())

wifi()
print("MAIN STARTED")

# ===============================
# SHT30
# ===============================

class SHT30:
    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        try:
            self.i2c.writeto(self.addr, b'\x2C\x06')
            time.sleep_ms(15)
            d = self.i2c.readfrom(self.addr, 6)
            t = -45 + 175 * ((d[0] << 8) + d[1]) / 65535
            h = 100 * ((d[3] << 8) + d[4]) / 65535
            return round(t,2), round(h,2)
        except:
            return 0,0

# ===============================
# TSL2591 (مختصر)
# ===============================

class TSL2591:
    def __init__(self, i2c, addr=0x29):
        self.i2c = i2c
        self.addr = addr
        try:
            self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
        except:
            pass

    def read(self):
        try:
            ch0 = self.i2c.readfrom_mem(self.addr, 0x14, 2)
            ch1 = self.i2c.readfrom_mem(self.addr, 0x16, 2)
            return int.from_bytes(ch0,"little"), int.from_bytes(ch1,"little")
        except:
            return 0,0

# ===============================
# VL53L0X (مختصر)
# ===============================

class VL53:
    def __init__(self, i2c, addr=0x29):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        try:
            self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
            time.sleep_ms(50)
            r = self.i2c.readfrom_mem(self.addr, 0x14, 2)
            return (r[0] << 8) | r[1]
        except:
            return 0

# ===============================
# I2C MAPS
# ===============================

# A1
i2c_a1 = I2C(0, scl=Pin(18), sda=Pin(19))
shtA_air  = SHT30(i2c_a1, 0x45)
tslA      = TSL2591(i2c_a1)
distA     = VL53(i2c_a1)

# A2
i2c_a2 = I2C(1, scl=Pin(5), sda=Pin(23))
shtA_w2   = SHT30(i2c_a2, 0x44)

# B1
i2c_b1 = SoftI2C(scl=Pin(26), sda=Pin(25))
shtB_air  = SHT30(i2c_b1, 0x45)
tslB      = TSL2591(i2c_b1)
distB     = VL53(i2c_b1)

# B2
i2c_b2 = SoftI2C(scl=Pin(32), sda=Pin(33))
shtB_w2 = SHT30(i2c_b2, 0x44)

# C1
i2c_c1 = SoftI2C(scl=Pin(4), sda=Pin(2))
shtC_air = SHT30(i2c_c1, 0x45)
tslC     = TSL2591(i2c_c1)
distC    = VL53(i2c_c1)

# C2
i2c_c2 = SoftI2C(scl=Pin(27), sda=Pin(14))
shtC_w2 = SHT30(i2c_c2, 0x44)

# ===============================
# Wind Sensor (GPIO13)
# ===============================

wind_pin = Pin(13, Pin.IN, Pin.PULL_UP)
wind_pulse = 0

def irq_wind(p):
    global wind_pulse
    wind_pulse += 1

wind_pin.irq(trigger=Pin.IRQ_FALLING, handler=irq_wind)

def get_wind():
    global wind_pulse
    wind_pulse = 0
    time.sleep(1)
    return wind_pulse * 2.4  # km/h

# ===============================
# ThingSpeak API KEYS
# ===============================

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"


# ===============================
# Send Function
# ===============================

def send_ts(api, **f):
    url = "https://api.thingspeak.com/update?api_key=" + api
    for k,v in f.items():
        url += f"&field{k}={v}"
    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except:
        print("TS ERROR")

# ===============================
# MAIN LOOP — SAFE CYCLING
# ===============================

while True:

    # -------- MODEL A --------
    Ta_air, Ha_air = shtA_air.read()
    Ta_w2,  Ha_w2  = shtA_w2.read()
    luxA, irA      = tslA.read()
    dist_A         = distA.read()

    send_ts(API_A,
        field1=dist_A,
        field2=Ta_air,
        field3=Ta_w2,
        field4=luxA,
        field5=irA
    )
    time.sleep(10)

    # -------- MODEL B --------
    Tb_air, Hb_air = shtB_air.read()
    Tb_w2,  Hb_w2  = shtB_w2.read()
    luxB, irB      = tslB.read()
    dist_B         = distB.read()

    send_ts(API_B,
        field1=dist_B,
        field2=Tb_air,
        field3=Tb_w2,
        field4=luxB,
        field5=irB
    )
    time.sleep(10)

    # -------- MODEL C --------
    Tc_air, Hc_air = shtC_air.read()
    Tc_w2,  Hc_w2  = shtC_w2.read()
    luxC, irC      = tslC.read()
    dist_C         = distC.read()

    send_ts(API_C,
        field1=dist_C,
        field2=Tc_air,
        field3=Tc_w2,
        field4=luxC,
        field5=irC
    )
    time.sleep(10)

    # -------- WIND --------
    w = get_wind()
    send_ts(API_W, field1=w)
    time.sleep(10)








   


