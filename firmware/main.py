import time, network, urequests
from machine import I2C, Pin
from lib.sht30 import SHT30

# WiFi
SSID = "HUAWEI-1006VE_Wi-Fi5"
PASS = "FPdGG9N7"

# ThingSpeak (قناة A)
API_KEY = "EU6EE36IJ7WSVYP3"

# Connect WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASS)
        while not wlan.isconnected():
            time.sleep(1)
    print("WiFi:", wlan.ifconfig())
    return wlan

connect_wifi()

# I2C for SHT30 (Model A1)
i2c = I2C(0, scl=Pin(18), sda=Pin(19))

# SHT30 (جرّب 0x44 أو 0x45 حسب حساسك)
sht = SHT30(i2c, addr=0x45)

while True:
    try:
        t, h = sht.measure()
        print("Temp:", t, "Humidity:", h)

        url = "https://api.thingspeak.com/update?api_key={}&field1={}&field2={}".format(
            API_KEY, t, h
        )

        r = urequests.get(url)
        print("ThingSpeak:", r.text)
        r.close()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(10)


