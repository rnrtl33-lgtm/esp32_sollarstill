import time
import network
import urequests
from machine import I2C, SoftI2C, Pin

# استدعاء مكتبة LTR390
from lib.ltr390 import LTR390

# ===============================
#  WiFi
# ===============================

WIFI_SSID = "Abdullah's phone"
WIFI_PASS = "42012999"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t = 20
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    print("WiFi:", wlan.ifconfig() if wlan.isconnected() else "FAILED")

wifi_connect()
print("MAIN STARTED")

# ===============================
# SHT30 Library
# ===============================

class SHT30:
    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        try:
            self.i2c.writeto(self.addr, b'\x2C\x06')
            time.sleep_ms(15)
            data = self.i2c.readfrom(self.addr, 6)
            temp = -45 + 175 * ((data[0] << 8) + data[1]) / 65535
            hum = 100 * ((data[3] << 8) + data[4]) / 65535
            return round(temp, 2), round(hum, 2)
        except:
            return 0, 0

# ===============================
# TSL2591 Library
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
            return int.from_bytes(ch0, "little"), int.from_bytes(ch1, "little")
        except:
            return 0, 0

# ===============================
# VL53L0X Simplified
# ===============================

class VL53L0X:
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
# I2C Buses — Model A
# ===============================

i2c_a1 = I2C(0, scl=Pin(18), sda=Pin(19))
i2c_a2 = I2C(1, scl=Pin(5),  sda=Pin(23))

sht_air_A = SHT30(i2c_a1)
sht_w2_A  = SHT30(i2c_a2)
uv_A      = LTR390(i2c_a1)
dist_A    = VL53L0X(i2c_a1)
tsl_A     = TSL2591(i2c_a1)

# ===============================
# I2C Buses — Model B
# ===============================

i2c_b1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_b2 = SoftI2C(scl=Pin(32), sda=Pin(33))

sht_air_B = SHT30(i2c_b1)
sht_w2_B  = SHT30(i2c_b2)
uv_B      = LTR390(i2c_b1)
dist_B    = VL53L0X(i2c_b1)
tsl_B     = TSL2591(i2c_b1)

# ===============================
# I2C Buses — Model C
# ===============================

i2c_c1 = SoftI2C(scl=Pin(4),  sda=Pin(2))
i2c_c2 = SoftI2C(scl=Pin(27), sda=Pin(14))

sht_air_C = SHT30(i2c_c1)
sht_w2_C  = SHT30(i2c_c2)
uv_C      = LTR390(i2c_c1)
dist_C    = VL53L0X(i2c_c1)
tsl_C     = TSL2591(i2c_c1)

# ===============================
# Wind Sensor (Speed only)
# ===============================

wind_pin = Pin(13, Pin.IN, Pin.PULL_UP)
wind_pulses = 0

def wind_irq(pin):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_FALLING, handler=wind_irq)

def get_wind_speed():
    global wind_pulses
    wind_pulses = 0
    time.sleep(1)  # measure pulses per second
    pps = wind_pulses
    return pps * 2.4   # km/h

# ===============================
# ThingSpeak APIs
# ===============================

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"

# ===============================
# FIXED send_ts FUNCTION
# ===============================

def send_ts(api, **fields):
    url = "https://api.thingspeak.com/update?api_key=" + api
    for k, v in fields.items():
        k = str(k)   # ← الحل الذي يمنع الخطأ
        url += f"&field{k}={v}"
    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except Exception as e:
        print("TS ERROR:", e)

# ===============================
# MAIN LOOP
# ===============================

while True:
    print("\nReading sensors...")

    # ========== MODEL A ==========
    t_air_A, h_air_A = sht_air_A.read()
    t_w2_A,  h_w2_A  = sht_w2_A.read()
    uvA = uv_A.read_uv()
    distA = dist_A.read()
    tslA_ch0, tslA_ch1 = tsl_A.read()

    send_ts(API_A,
        **{
            1: uvA,
            2: distA,
            3: t_air_A,
            4: t_w2_A,
            5: tslA_ch0,
            6: tslA_ch1
        }
    )

    # ========== MODEL B ==========
    t_air_B, h_air_B = sht_air_B.read()
    t_w2_B,  h_w2_B  = sht_w2_B.read()
    uvB = uv_B.read_uv()
    distB = dist_B.read()
    tslB_ch0, tslB_ch1 = tsl_B.read()

    send_ts(API_B,
        **{
            1: uvB,
            2: distB,
            3: t_air_B,
            4: t_w2_B,
            5: tslB_ch0,
            6: tslB_ch1
        }
    )

    # ========== MODEL C ==========
    t_air_C, h_air_C = sht_air_C.read()
    t_w2_C,  h_w2_C  = sht_w2_C.read()
    uvC = uv_C.read_uv()
    distC = dist_C.read()
    tslC_ch0, tslC_ch1 = tsl_C.read()

    send_ts(API_C,
        **{
            1: uvC,
            2: distC,
            3: t_air_C,
            4: t_w2_C,
            5: tslC_ch0,
            6: tslC_ch1
        }
    )

    # ========== WIND ==========
    wind_speed = get_wind_speed()
    send_ts(API_W,
        **{
            1: wind_speed
        }
    )

    print("Waiting 30s...")
    time.sleep(30)







   


