import time
import network
import urequests
from machine import I2C, Pin

# ================================
#  WiFi Configuration
# ================================
SSID = "HUAWEI-1006VE_Wi-Fi5"
PASS = "FPdGG9N7"

# ================================
#  ThingSpeak API Key (A Model)
# ================================
API_A = "EU6EE36IJ7WSVYP3"

# ================================
#  Connect to WiFi
# ================================
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(SSID, PASS)
        t = 20
        while not wlan.isconnected() and t > 0:
            print("Connecting...")
            time.sleep(1)
            t -= 1

    print("WiFi:", wlan.ifconfig())

wifi_connect()

# ================================
#  Libraries
# ================================
from lib.sht30 import SHT30
from lib.vl53l0x import VL53L0X
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591

# ================================
#  I2C Bus for Model A
# ================================
i2c_a1 = I2C(0, scl=Pin(18), sda=Pin(19))  # LTR390 + VL53 + SHT30-Air + TSL2591
i2c_a2 = I2C(1, scl=Pin(5),  sda=Pin(23))  # SHT30-Water

# ================================
#  Initialize Sensors
# ================================
sht_air  = SHT30(i2c_a1, addr=0x45)
ltr      = LTR390(i2c_a1)
vl53     = VL53L0X(i2c_a1)
tsl      = TSL2591(i2c_a1)
sht_w2   = SHT30(i2c_a2, addr=0x44)

# ================================
#  Safe Read Wrapper
# ================================
def safe(f, default=0):
    try:
        return f()
    except:
        return default

# ================================
#  Send to ThingSpeak
# ================================
def send_ts(api, **fields):
    url = "https://api.thingspeak.com/update?api_key=" + api
    for k, v in fields.items():
        url += f"&{k}={v}"

    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except:
        print("TS ERROR")

# ================================
#  MAIN LOOP (Model A Only)
# ================================
print("MAIN STARTED - MODEL A ONLY")

while True:

    # Read Temperature / Humidity
    t_air, h_air = safe(lambda: sht_air.read(), (0,0))
    t_w2,  h_w2  = safe(lambda: sht_w2.read(),  (0,0))

    # Read UV
    uv = safe(lambda: ltr.read_uv())

    # Read Distance
    dist = safe(lambda: vl53.read())

    # Read Light
    lux = safe(lambda: tsl.lux())
    ir  = safe(lambda: tsl.ir())

    # Send to ThingSpeak
    send_ts(API_A,
        field1=t_air,
        field2=uv,
        field3=dist,
        field4=t_air,
        field5=t_w2,
        field6=lux,
        field7=ir,
        field8=h_air  # مجرد تعبئة لكي لا يبقى فارغ
    )

    print("A SENT. Sleeping 15 seconds...\n")
    time.sleep(15)









   


