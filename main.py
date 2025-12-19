# ================= main.py =================
import time, gc
from machine import Pin, SoftI2C
import urequests

# ---------- ThingSpeak ----------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8GG8DF40LCGV99"

def send_ts(api, f1, f2, f3=None, f4=None):
    url = "http://api.thingspeak.com/update?api_key={}&field1={}&field2={}".format(api, f1, f2)
    if f3 is not None:
        url += "&field3={}".format(f3)
    if f4 is not None:
        url += "&field4={}".format(f4)

    r = urequests.get(url)
    print("TS:", r.status_code, r.text)
    r.close()
    time.sleep(2)

# ---------- I2C ----------
i2cA = SoftI2C(sda=Pin(19), scl=Pin(18))
i2cB = SoftI2C(sda=Pin(25), scl=Pin(26))
i2cC = SoftI2C(sda=Pin(32), scl=Pin(14))
i2cD = SoftI2C(sda=Pin(15), scl=Pin(2))

from lib.sht30_clean import SHT30
from lib.vl53l0x_clean import VL53L0X
from lib.ltr390_clean import LTR390
from lib.tsl2591_fixed import TSL2591

# ---------- Sensors ----------
A_air = SHT30(i2cA, 0x45)
A_wat = SHT30(i2cA, 0x44)
A_dist = VL53L0X(i2cA)

B_air = SHT30(i2cB, 0x45)
B_wat = SHT30(i2cB, 0x44)
B_dist = VL53L0X(i2cB)

C_air = SHT30(i2cC, 0x45)
C_wat = SHT30(i2cC, 0x44)
C_dist = VL53L0X(i2cC)

D_uv = LTR390(i2cD)
D_lux = TSL2591(i2cD)

print("=== MAIN RUNNING ===")

while True:
    # ----- A (الذي نجح) -----
    Ta,_ = A_air.measure()
    Twa,_ = A_wat.measure()
    Da = A_dist.read()
    print("A:", Ta, Twa, Da)
    send_ts(API_A, round(Ta,2), round(Twa,2), Da)
    time.sleep(20)

    # ----- B -----
    Tb,_ = B_air.measure()
    Twb,_ = B_wat.measure()
    Db = B_dist.read()
    print("B:", Tb, Twb, Db)
    send_ts(API_B, round(Tb,2), round(Twb,2), Db)
    time.sleep(20)

    # ----- C -----
    Tc,_ = C_air.measure()
    Twc,_ = C_wat.measure()
    Dc = C_dist.read()
    print("C:", Tc, Twc, Dc)
    send_ts(API_C, round(Tc,2), round(Twc,2), Dc)
    time.sleep(20)

    # ----- D -----
    UV = D_uv.read_uv()
    full, ir = D_lux.get_raw_luminosity()
    lux = D_lux.calculate_lux(full, ir)
    print("D:", UV, ir, lux)
    send_ts(API_D, UV, ir, round(lux,1))
    time.sleep(300)

    gc.collect()
