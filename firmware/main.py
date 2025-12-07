import time, network, urequests
from machine import I2C, SoftI2C, Pin
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

print("MAIN STARTED")


# =====================================================
#                     I2C BUSES
# =====================================================

# ----- A1 -----
i2c_A1 = I2C(0, scl=Pin(18), sda=Pin(19))   # Hardware I2C

# ----- A2 -----
i2c_A2 = I2C(1, scl=Pin(5), sda=Pin(23))    # Hardware I2C

# ----- B1 -----
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))  # Soft I2C

# ----- B2 -----
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))  # Soft I2C


# =====================================================
#                     SENSORS A
# =====================================================

print("Init sensors A...")

# A1
sht_ambient = SHT30(i2c_A1, addr=0x45)
ltr_a = LTR390(i2c_A1, addr=0x53)
vl_a = VL53L0X(i2c_A1)

# A2
sht_air = SHT30(i2c_A2, addr=0x45)
sht_water = SHT30(i2c_A2, addr=0x44)
tsl_a = TSL2591(i2c_A2)


# =====================================================
#                     SENSORS B
# =====================================================

print("Init sensors B...")

# B1
ltr_b = LTR390(i2c_B1, addr=0x53)
vl_b = VL53L0X(i2c_B1)

# B2
sht_air_b = SHT30(i2c_B2, addr=0x45)
sht_water_b = SHT30(i2c_B2, addr=0x44)
tsl_b = TSL2591(i2c_B2)


# =====================================================
#                  THINGSPEAK API
# =====================================================

API_KEY = "EU6EE36IJ7WSVYP3"   # قناة A + B الآن في نفس القناة

def send_data(params):
    url = "https://api.thingspeak.com/update?api_key=" + API_KEY
    for field, val in params.items():
        url += f"&field{field}={val}"
    try:
        r = urequests.get(url)
        print("TS:", r.text)
        r.close()
    except Exception as e:
        print("ThingSpeak ERR:", e)


# =====================================================
#                       LOOP
# =====================================================

while True:
    try:
        # ----------- A1 -----------
        t_amb, h_amb = sht_ambient.measure()
        uv_a = ltr_a.read_uv()
        lux_a = ltr_a.read_lux()
        dist_a = vl_a.read()

        # ----------- A2 -----------
        t_air, h_air = sht_air.measure()
        t_water, h_water = sht_water.measure()
        vis_a, ir_a = tsl_a.read()

        # ----------- B1 -----------
        uv_b = ltr_b.read_uv()
        lux_b = ltr_b.read_lux()
        dist_b = vl_b.read()

        # ----------- B2 -----------
        t_air_b, h_air_b = sht_air_b.measure()
        t_water_b, h_water_b = sht_water_b.measure()
        vis_b, ir_b = tsl_b.read()

        # Debug print
        print("A1 Ambient:", t_amb, h_amb)
        print("A1 LTR:", uv_a, lux_a)
        print("A1 VL:", dist_a)
        print("A2 Air:", t_air, h_air)
        print("A2 Water:", t_water, h_water)
        print("A2 TSL:", vis_a, ir_a)

        print("B1 LTR:", uv_b, lux_b)
        print("B1 VL:", dist_b)
        print("B2 Air:", t_air_b, h_air_b)
        print("B2 Water:", t_water_b, h_water_b)
        print("B2 TSL:", vis_b, ir_b)

        # Sending data
        send_data({
            1: t_amb,
            2: t_air,
            3: t_water,
            4: uv_a,
            5: lux_a,
            6: dist_a,
            7: t_air_b,
            8: t_water_b,
            9: uv_b,
            10: lux_b,
            11: dist_b
        })

    except Exception as e:
        print("ERR:", e)

    time.sleep(20)




   


