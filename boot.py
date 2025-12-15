import network, time, urequests, os

WIFI_SSID = "Abdullah's phone"
WIFI_PASS = "42012999"

RAW_MAIN = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi OK:", wlan.ifconfig())

def update_main():
    try:
        r = urequests.get(RAW_MAIN)
        new = r.text
        r.close()
        if new:
            with open("main.py", "w") as f:
                f.write(new)
            print("main.py updated.")
    except:
        print("Could not fetch main.py")

connect_wifi()

if "main.py" not in os.listdir():
    update_main()
else:
    print("main.py exists.")

print("Boot done → running main.py")
