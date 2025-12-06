
import network, urequests, os, machine, time

# ==========================
#     WIFI SETTINGS
# ==========================
SSID = "YOUR_WIFI_NAME"
PASS = "YOUR_WIFI_PASSWORD"

# ==========================
#     OTA FILE SOURCE
# ==========================
GITHUB_MAIN = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/firmware/main.py"
LOCAL_MAIN = "main.py"


# ==========================
#      CONNECT WIFI
# ==========================
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASS)

        timeout = 20
        while timeout > 0 and not wlan.isconnected():
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
    else:
        print("WiFi failed.")


# ==========================
#         OTA UPDATE
# ==========================
def ota_update():
    try:
        print("Checking for updates...")

        r = urequests.get(GITHUB_MAIN)
        if r.status_code != 200:
            print("GitHub error:", r.status_code)
            return
        new_code = r.text
        r.close()

        if LOCAL_MAIN not in os.listdir():
            print("Downloading main.py...")
            with open(LOCAL_MAIN, "w") as f:
                f.write(new_code)
            print("Main.py downloaded → rebooting.")
            time.sleep(1)
            machine.reset()

        else:
            with open(LOCAL_MAIN, "r") as f:
                old_code = f.read()

            if old_code != new_code:
                print("New version found → Updating main.py...")
                with open(LOCAL_MAIN, "w") as f:
                    f.write(new_code)
                print("Updated → rebooting.")
                time.sleep(1)
                machine.reset()
            else:
                print("Already up to date.")

    except Exception as e:
        print("OTA ERROR:", e)


# ==========================
#        RUN SEQUENCE
# ==========================
wifi_connect()
ota_update()

print("Boot complete → running main.py")
