from machine import Pin, SoftI2C, reset
import time, gc, machine
import network, urequests, os

from sht30_clean import SHT30
from vl53l0x_clean import VL53L0X
from hx711_clean import HX711
from ltr390_uva import LTR390
from tsl2591_mp import TSL2591


SSID = "stc_wifi_8105"
PASSWORD = "bfw6qtn7tu3"

GITHUB_RAW = "https://raw.githubusercontent.com/rnrt133-lgtm/esp32_solarstill/main/main.py"

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

TS_URL = "https://api.thingspeak.com/update"

SEND_INTERVAL = 180
SAMPLE_INTERVAL = 10
SAMPLES = SEND_INTERVAL // SAMPLE_INTERVAL

AUTO_RESET_INTERVAL = 6 * 60 * 60
BOOT_TIME = time.time()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                return True
            time.sleep(1)
    return wlan.isconnected()


def ota_update():
    try:
        r = urequests.get(GITHUB_RAW)
        if r.status_code == 200:
            with open("main.py", "w") as f:
                f.write(r.text)
        r.close()
    except:
        pass


def send_ts(api, f1, f2, f3, f4):
    try:
        r = urequests.get(
            "{}?api_key={}&field1={}&field2={}&field3={}&field4={}".format(
                TS_URL, api, f1, f2, f3, f4
            )
        )
        r.close()
    except:
        pass


connect_wifi()
ota_update()

i2c_a = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_c = SoftI2C(scl=Pin(14), sda=Pin(27))
i2c_d = SoftI2C(scl=Pin(5),  sda=Pin(23))

air_a = SHT30(i2c_a, 0x45)
water_a = SHT30(i2c_a, 0x44)
laser_a = VL53L0X(i2c_a)
hx_a = HX711(dt=34, sck=33)
hx_a.offset = -124129.5
hx_a.scale = 641.46344
time.sleep(2)
hx_a.tare()

air_c = SHT30(i2c_c, 0x45)
water_c = SHT30(i2c_c, 0x44)
laser_c = VL53L0X(i2c_c)
hx_c = HX711(dt=36, sck=16)
hx_c.offset = -1222087.8
hx_c.scale = 705.81304
time.sleep(2)
hx_c.tare()

uv = LTR390(i2c_d, gain=3, resolution=18)
light = TSL2591(i2c_d, gain=0x10, integration=0x01)

sumA = [0,0,0,0]
sumC = [0,0,0,0]
count = 0

while True:
    try:
        Ta,_ = air_a.measure()
        Wa,_ = water_a.measure()
        Da = laser_a.read() / 10
        Ga = hx_a.get_weight()

        Tc,_ = air_c.measure()
        Wc,_ = water_c.measure()
        Dc = laser_c.read() / 10
        Gc = hx_c.get_weight()

        sumA[0]+=Ta; sumA[1]+=Wa; sumA[2]+=Da; sumA[3]+=Ga
        sumC[0]+=Tc; sumC[1]+=Wc; sumC[2]+=Dc; sumC[3]+=Gc

        count += 1

        if count >= SAMPLES:
            avgA = [x/count for x in sumA]
            avgC = [x/count for x in sumC]

            send_ts(API_A, avgA[0], avgA[1], avgA[2], avgA[3])
            send_ts(API_B, avgA[0], avgA[1], avgA[2], avgA[3])
            send_ts(API_C, avgC[0], avgC[1], avgC[2], avgC[3])
            send_ts(API_D, uv.uva_raw(), light.lux(), light.infrared(), 0)

            sumA = [0,0,0,0]
            sumC = [0,0,0,0]
            count = 0

        if time.time() - BOOT_TIME > AUTO_RESET_INTERVAL:
            machine.reset()

        gc.collect()
        time.sleep(SAMPLE_INTERVAL)

    except:
        time.sleep(5)
