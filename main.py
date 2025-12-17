
import time, gc
from machine import Pin, SoftI2C, reset

 
from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X
from lib.hx711_simple import HX711

 
 
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_D = "HG8G8BDF40LCGV99"

 
# I2C BUSES
 
# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15))

 
hxA = HX711(34, 33)
hxB = HX711(35, 33)
hxC = HX711(36, 33)

 
A = {
    "amb": SHT30(i2c_A1, 0x45),
    "air": SHT30(i2c_A2, 0x45),
    "wat": SHT30(i2c_A2, 0x44),
    "uv":  LTR390(i2c_A1),
    "lux": TSL2591(i2c_A2),
    "dis": VL53L0X(i2c_A1),
    "hx":  hxA
}

B = {
    "air": SHT30(i2c_B2, 0x45),
    "wat": SHT30(i2c_B2, 0x44),
    "uv":  LTR390(i2c_B1),
    "lux": TSL2591(i2c_B2),
    "dis": VL53L0X(i2c_B1),
    "hx":  hxB
}

C = {
    "air": SHT30(i2c_C2, 0x45),
    "wat": SHT30(i2c_C2, 0x44),
    "uv":  LTR390(i2c_C1),
    "lux": TSL2591(i2c_C2),
    "dis": VL53L0X(i2c_C1),
    "hx":  hxC
}

 
def send_ts(api, data):
    try:
        url = "https://api.thingspeak.com/update?api_key=" + api
        i = 1
        for v in data.values():
            url += "&field{}={}".format(i, v)
            i += 1
        import urequests
        r = urequests.get(url)
        r.close()
    except Exception as e:
        print("TS error:", e)

 
def read_model(m, with_amb=False):
    out = {}

    if with_amb:
        t,h = m["amb"].measure()
        out["T_amb"] = t
        out["H_amb"] = h

    t,h = m["air"].measure()
    out["T_air"] = t
    out["H_air"] = h

    t,h = m["wat"].measure()
    out["T_wat"] = t
    out["H_wat"] = h

    out["ALS"] = m["uv"].read_als()
    out["UV"]  = m["uv"].read_uv()

    full, ir = m["lux"].get_raw_luminosity()
    out["LUX"] = m["lux"].calculate_lux(full, ir)
    out["IR"]  = ir

    try:
        out["DIST_mm"] = m["dis"].read()
    except:
        out["DIST_mm"] = None

    out["WEIGHT_g"] = m["hx"].get_weight()

    return out

 
print("\n>>> MAIN RUNNING (A+B+C+D) <<<\n")

cycle = 0

while True:
    dataA = read_model(A, True)
    dataB = read_model(B)
    dataC = read_model(C)
    dataD = {"WIND_m_s": 0.0}

    print("A:", dataA)
    print("B:", dataB)
    print("C:", dataC)
    print("D:", dataD)
    print("-" * 70)

    send_ts(API_A, dataA)
    send_ts(API_B, dataB)
    send_ts(API_C, dataC)
    send_ts(API_D, dataD)

    cycle += 1
    if cycle >= 15:       
        print("Auto reset for OTA...")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
