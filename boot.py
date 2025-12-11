
import network, urequests, os, machine, time

SSID = "HUAWEI-1006VE_Wi-Fi5"   # عدّلها عند الحاجة
PASS = "FPdGG9N7"

GITHUB_MAIN = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"
LOCAL_MAIN = "main.py"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASS)

        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    
    if wlan.isconnected():
        print("WiFi:", wlan.ifconfig())
    else:
        print("WiFi: FAILED")

def ota_update():
    try:
        print("Checking GitHub for updates...")
        r = urequests.get(GITHUB_MAIN)

        if r.status_code != 200:
            print("GitHub Error:", r.status_code)
            return

        remote = r.text
        r.close()

        # إذا لا يوجد main.py → نزله لأول مرة
        if LOCAL_MAIN not in os.listdir():
            print("Downloading main.py (first time)...")
            with open(LOCAL_MAIN, "w") as f:
                f.write(remote)
            machine.reset()

        # إذا يوجد → قارن النص
        with open(LOCAL_MAIN, "r") as f:
            local = f.read()

        if local != remote:
            print("New version found → Updating...")
            with open(LOCAL_MAIN, "w") as f:
                f.write(remote)
            machine.reset()
        else:
            print("main.py already latest.")

    except Exception as e:
        print("OTA ERROR:", e)

wifi_connect()
ota_update()

print("Boot.py OK → Running main.py")

