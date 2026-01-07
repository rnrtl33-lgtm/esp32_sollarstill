from machine import Pin, SoftI2C
import time, gc, machine
import network, urequests

from sht30_clean import SHT30
from vl53l0x_clean import VL53L0X
from hx711_clean import HX711
from ltr390_uva import LTR390
from tsl2591_mp import TSL2591


# WIFI
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qtnu3"

def wifi_connected():
    return network.WLAN(network.STA_IF).isconnected()

def ensure_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        for _ in range(15):
            if wlan.isconnected():
                print("WiFi connected")
                return True
            time.sleep(1)
        print("WiFi not connected")
        return False
    return True


# THINGSPEAK C

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

TS_URL = "https://api.thingspeak.com/update"
SEND_INTERVAL = 20 * 60    # 20 minutes (stable)

def send_ts(api, f1, f2, f3, f4):
    if not wifi_connected():
        return
    try:
        url = "{}?api_key={}&field1={}&field2={}&field3={}&field4={}".format(
            TS_URL, api, f1, f2, f3, f4
        )
        r = urequests.get(url)
        r.close()
    except:
        pass



BOOT_TIME = time.time()
AUTO_RESET_INTERVAL = 12 * 60 * 60   # 12 hours


i2c_a = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_b = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_c = SoftI2C(scl=Pin(14), sda=Pin(27))
i2c_d = SoftI2C(scl=Pin(5),  sda=Pin(23))


# MODEL A

air_a   = SHT30(i2c_a, 0x45)
water_a = SHT30(i2c_a, 0x44)
laser_a = VL53L0X(i2c_a)
hx_a = HX711(dt=34, sck=33)

hx_a.offset = -124129.5
hx_a.scale  = 641.46344

LASER_REF_A = 13.8   # cm
WEIGHT_FACTOR_A = 1.53

# MODEL B

air_b   = SHT30(i2c_b, 0x45)
water_b = SHT30(i2c_b, 0x44)
laser_b = VL53L0X(i2c_b)
hx_b = HX711(dt=35, sck=32)

hx_b.offset = 1477.0
hx_b.scale  = 389.7205

LASER_REF_B = 6.3   # cm


# MODEL C

air_c   = SHT30(i2c_c, 0x45)
water_c = SHT30(i2c_c, 0x44)
laser_c = VL53L0X(i2c_c)
hx_c = HX711(dt=36, sck=16)

hx_c.offset = -1222087.8
hx_c.scale  = 705.81304


# MODEL D

uv = LTR390(i2c_d, gain=3, resolution=18)
light = TSL2591(i2c_d, gain=0x10, integration=0x01)

# RELAY (PUMP)

RELAY_PIN = Pin(4, Pin.OUT)
RELAY_PIN.value(1)   # OFF


time.sleep(3)
hx_a.tare()
hx_b.tare()
hx_c.tare()

ensure_wifi()

print("\nSYSTEM STARTED – FINAL MODE\n")


while True:
    try:
        #MODEL A
        t_air_a, _   = air_a.measure()
        t_water_a, _ = water_a.measure()
        raw_a = laser_a.read() / 10
        dist_a = LASER_REF_A - raw_a
        weight_a = hx_a.get_weight() * WEIGHT_FACTOR_A

        print("A DIST:", dist_a, "cm")

        send_ts(API_A, t_air_a, t_water_a, dist_a, weight_a)

        #MODEL B 
        t_air_b, _   = air_b.measure()
        t_water_b, _ = water_b.measure()
        raw_b = laser_b.read() / 10
        dist_b = LASER_REF_B - raw_b
        weight_b = hx_b.get_weight()

        print("B DIST:", dist_b, "cm")

        send_ts(API_B, t_air_b, t_water_b, dist_b, weight_b)

        #RELAY CONTROL
        if dist_a > 15 or dist_b > 15:
            RELAY_PIN.value(0)   # ON
        else:
            RELAY_PIN.value(1)   # OFF

        #MODEL C
        t_air_c, _   = air_c.measure()
        t_water_c, _ = water_c.measure()
        dist_c = laser_c.read() / 10
        weight_c = hx_c.get_weight()

        print("C DIST:", dist_c, "cm")

        send_ts(API_C, t_air_c, t_water_c, dist_c, weight_c)

        #MODEL D
        uva = uv.uva_raw()
        ir  = light.infrared()
        lux = light.lux()

        send_ts(API_D, uva, lux, ir, 0)

        -
        gc.collect()
        time.sleep(SEND_INTERVAL)

        #AUTO RESET 
        if time.time() - BOOT_TIME > AUTO_RESET_INTERVAL:
            print("AUTO RESET (12H)")
            time.sleep(2)
            machine.reset()

    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        gc.collect()
        time.sleep(30)
