import network, time, urequests, os, machine

WIFI_SSID = "Hassan"
WIFI_PASS = "H7654321"

RAW_URL = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.4)

    print("WiFi OK:", wlan.ifconfig())


def get_remote_code():
    print("Checking GitHub...")
    r = urequests.get(RAW_URL)
    txt = r.text
    r.close()
    return txt


def get_local_code():
    if "main.py" not in os.listdir():
        return None
    try:
        with open("main.py", "r") as f:
            return f.read()
    except:
        return None


def update_main():
    try:
        remote = get_remote_code()
        local  = get_local_code()

        if local is None:
            print("Local main.py missing → downloading new copy.")
            with open("main.py", "w") as f:
                f.write(remote)
            print("main.py saved (first install).")
            return True

        if remote.strip() != local.strip():
            print("New version detected → updating main.py ...")
            with open("main.py", "w") as f:
                f.write(remote)
            print("✔️ Update finished.")
            return True

        print("No update needed.")
        return False

    except Exception as e:
        print("Update error:", e)
        return False



wifi_connect()
changed = update_main()

print("Boot.py OK → Running main.py")

try:
    import main
except Exception as e:
    print("main.py error:", e)
