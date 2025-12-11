
import network, time, urequests, os

WIFI_SSID = "HUAWEI-1006VE_Wi-Fi5"
WIFI_PASS = "FPdGG9N7"
RAW_URL = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi:", wlan.ifconfig())

def download_main():
    try:
        print("Checking GitHub for updates...")
        r = urequests.get(RAW_URL)
        new_code = r.text
        r.close()

        if not new_code:
            print("Error: Empty file")
            return

        with open("main.py", "w") as f:
            f.write(new_code)

        print("main.py updated.")
    except Exception as e:
        print("Update failed:", e)

wifi_connect()

if "main.py" not in os.listdir():
    print("Downloading main.py (first time)...")
    download_main()
else:
    print("main.py already exists.")

print("Boot.py OK → Running main.py")

import main

