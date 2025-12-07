import time, network, urequests
from machine import I2C, Pin
from lib.sht30 import SHT30
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.vl53l0x import VL53L0X

# -----------------------------
# WiFi
# -----------------------------
SSID = "HUAWEI-1006VE_Wi-Fi5"
PASS = "FPdGG9N7"

def wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASS)
        while not wlan.isconnected():
            time.sleep(1)
    print("WiFi:", wlan.ifconfig())

wifi()

# -----------------------------
# I2C Buses of Model A
# -----------------------------
print("MAIN STARTED")

# A1 bus → SDA19 / SCL18
i2c_A1 = I2C(0, scl=Pin(18), sda=Pin(19))

# A2 bus → SDA23 / SCL5
i2c_A2 = I2C(1, scl=Pin(5), sda=Pin(23))

print("Init sensors...")

# -----------------------------
# Sensors A1
# -----------------------------
sht_ambient = SHT30(i2c_A1, addr=0x45)   # SHT30 Ambient
ltr_a = LTR390(i2c_A1, addr=0x53)         # LTR390
vl_a = VL53L0X(i2c_A1)                    # Distance
vl_a.start()

# -----------------------------
# Sensors A2
# -----------------------------
sht_air = SHT30(i2c_A2, addr=0x45)        # SHT30 Air
sht_water = SHT30(i2c_A2, addr=0x44)      # SHT30 Water
tsl = TSL2591(i2c_A2)                     # TSL2591


# -----------------------------
# ThingSpeak
# -----------------------------
API_KEY = "EU6EE36IJ7WSVYP3"

def send_data(params):
    base = "https://api.thingspeak.com/update?api_key=" + API_KEY
    for i, val in params.items():
        base += f"&field{i}={val}"
    try:
        r = urequests.get(base)
        print("TS:", r.text)
        r.close()
    except:
        print("ThingSpeak Error")


# -----------------------------
# Loop
# -----------------------------
while True:
    try:
        # A1 readings
        t_amb, h_amb = sht_ambient.measure()
        uv = ltr_a.read_uv()
        als = ltr_a.read_lux()
        dist = vl_a.read()

        # A2 readings
        t_air, h_air = sht_air.measure()
        t_water, h_water = sht_water.measure()
        (vis, ir) = tsl.read()

        print("Ambient:", t_amb, h_amb)
        print("Air:", t_air, h_air)
        print("Water:", t_water, h_water)
        print("UV:", uv, "Lux:", als)
        print("Distance:", dist)
        print("TSL:", vis, ir)

        send_data({
            1: t_amb,
            2: h_amb,
            3: t_air,
            4: t_water,
            5: uv,
            6: als,
            7: dist
        })

    except Exception as e:
        print("ERR:", e)

    time.sleep(20)   # ThingSpeak limit



   


