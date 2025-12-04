 print("main.py running...")
print("Initializing I2C buses...")

from machine import Pin, SoftI2C
from time import sleep, localtime, ticks_ms, ticks_diff
import urequests
import time

# ======================================================
#  CONFIG: ThingSpeak API keys
# ======================================================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"


# ======================================================
#  Safe sender to ThingSpeak (never crashes)
# ======================================================
def send_to_thingspeak(api_key, fields):
    url = "https://api.thingspeak.com/update"
    payload = "api_key=" + api_key
    for i, v in enumerate(fields, start=1):
        if v is None:
            v = 0
        payload += "&field{}={}".format(i, v)
    try:
        r = urequests.post(url, data=payload)
        r.close()
        print("→ TS:", api_key[:6], fields)
    except Exception as e:
        print("TS error:", e)


# ======================================================
#   I2C Bus Setup
# ======================================================
i2c_A1 = SoftI2C(sda=Pin(19), scl=Pin(18), freq=100000)
i2c_A2 = SoftI2C(sda=Pin(23), scl=Pin(5),  freq=100000)

i2c_B1 = SoftI2C(sda=Pin(25), scl=Pin(26), freq=100000)
i2c_B2 = SoftI2C(sda=Pin(27), scl=Pin(14), freq=100000)

i2c_C1 = SoftI2C(sda=Pin(32), scl=Pin(0),  freq=50000)
i2c_C2 = SoftI2C(sda=Pin(15), scl=Pin(2),  freq=50000)

print("I2C ready.")


# ======================================================
#   Import SHT30 (Temperature)
# ======================================================
from lib.sht30 import SHT30

# Model A
sht_air_A = SHT30(i2c_A2, addr=0x45)
sht_w2_A  = SHT30(i2c_A2, addr=0x44)
sht_amb   = SHT30(i2c_A1, addr=0x45)

# Model B
sht_air_B = SHT30(i2c_B2, addr=0x45)
sht_w2_B  = SHT30(i2c_B2, addr=0x44)

# Model C
sht_air_C = SHT30(i2c_C2, addr=0x45)
sht_w2_C  = SHT30(i2c_C2, addr=0x44)


def safe_read_sht(sht):
    try:
        t, rh = sht.measure()
        return t, rh
    except:
        return 0, 0


# ======================================================
#   Load Cell HX711 (Mass)
# ======================================================
from lib.hx711 import HX711

hxA = HX711(34, 33); hxA.set_scale(1.0)
hxB = HX711(35, 33); hxB.set_scale(1.0)
hxC = HX711(36, 33); hxC.set_scale(1.0)

try:
    hxA.tare(); hxB.tare(); hxC.tare()
except:
    pass

def safe_mass(hx):
    try:
        return hx.get_units(5)
    except:
        return 0


# ======================================================
#  LTR390 UV Sensor
# ======================================================
LTR = 0x53
def ltr_read(bus):
    try:
        bus.writeto_mem(LTR, 0x00, b'\x06')
        sleep(0.05)
        data = bus.readfrom_mem(LTR, 0x10, 3)
        uv = data[0] | (data[1] << 8) | (data[2] << 16)
        return uv, uv / 2300
    except:
        return 0, 0


# ======================================================
#  TSL2591 LIGHT SENSOR (IR + Lux)
# ======================================================
from lib.tsl2591 import TSL2591

tsl_A = TSL2591(i2c_A2)
tsl_B = TSL2591(i2c_B2)
tsl_C = TSL2591(i2c_C2)

def safe_tsl(tsl):
    try:
        return tsl.read_ir_lux()
    except:
        return 0, 0


# ======================================================
#  VL53L0X Distance
# ======================================================
def vl_read(bus):
    try:
        bus.writeto_mem(0x29, 0x00, b'\x01')
        sleep(0.05)
        hi = bus.readfrom_mem(0x29, 0x1E, 1)[0]
        lo = bus.readfrom_mem(0x29, 0x1F, 1)[0]
        return (hi << 8) | lo
    except:
        return 0


# ======================================================
#  Wind speed sensor
# ======================================================
wind_pin = Pin(13, Pin.IN)
wind_count = 0
last_ms = ticks_ms()

def wind_irq(pin):
    global wind_count
    wind_count += 1

wind_pin.irq(trigger=Pin.IRQ_FALLING, handler=wind_irq)

def read_wind():
    global wind_count, last_ms
    now = ticks_ms()
    dt = ticks_diff(now, last_ms) / 1000
    if dt <= 0:
        return 0, None
    pulses = wind_count
    wind_count = 0
    last_ms = now
    speed = pulses * 1.0
    return speed, None


# ======================================================
#  Formatting helper
# ======================================================
def fmt(x, w=6, p=2):
    try:
        return ("{:"+str(w)+"."+str(p)+"f}").format(x)
    except:
        return "   0.00"


# ======================================================
#  Print Header
# ======================================================
print("""
==================== SENSOR TABLE ====================
[A] T_air | T_w2 | Tamb | UV | UVI | IR | Lux | Dist | Mass
[B] T_air | T_w2 | UV | UVI | IR | Lux | Dist | Mass
[C] T_air | T_w2 | UV | UVI | IR | Lux | Dist | Mass
[W] Wind Speed
=======================================================
""")


# ======================================================
#  MAIN LOOP (every 30 seconds)
# ======================================================
PERIOD = 30
print("Starting sensor loop...\n")

while True:

    # MODEL A
    Ta,_    = safe_read_sht(sht_air_A)
    Tw2a,_  = safe_read_sht(sht_w2_A)
    Tamb,_  = safe_read_sht(sht_amb)
    uvA,uviA = ltr_read(i2c_A1)
    irA,luxA = safe_tsl(tsl_A)
    distA    = vl_read(i2c_A1)
    massA    = safe_mass(hxA)

    # MODEL B
    Tb,_    = safe_read_sht(sht_air_B)
    Tw2b,_  = safe_read_sht(sht_w2_B)
    uvB,uviB = ltr_read(i2c_B1)
    irB,luxB = safe_tsl(tsl_B)
    distB    = vl_read(i2c_B1)
    massB    = safe_mass(hxB)

    # MODEL C
    Tc,_    = safe_read_sht(sht_air_C)
    Tw2c,_  = safe_read_sht(sht_w2_C)
    uvC,uviC = ltr_read(i2c_C1)
    irC,luxC = safe_tsl(tsl_C)
    distC    = vl_read(i2c_C1)
    massC    = safe_mass(hxC)

    # WIND
    wind_speed, wind_dir = read_wind()

    # PRINT TABLE
    print("-------------------------------------------------------")
    print(f"[A] {fmt(Ta)} | {fmt(Tw2a)} | {fmt(Tamb)} | {fmt(uvA,5,0)} | {fmt(uviA,5,2)} | {fmt(irA,6,0)} | {fmt(luxA,6,0)} | {fmt(distA,6,0)} | {fmt(massA,6,2)}")
    print(f"[B] {fmt(Tb)} | {fmt(Tw2b)} | {fmt(uvB,5,0)} | {fmt(uviB,5,2)} | {fmt(irB,6,0)} | {fmt(luxB,6,0)} | {fmt(distB,6,0)} | {fmt(massB,6,2)}")
    print(f"[C] {fmt(Tc)} | {fmt(Tw2c)} | {fmt(uvC,5,0)} | {fmt(uviC,5,2)} | {fmt(irC,6,0)} | {fmt(luxC,6,0)} | {fmt(distC,6,0)} | {fmt(massC,6,2)}")
    print(f"[W] Wind Speed = {fmt(wind_speed,6,2)}")
    print("-------------------------------------------------------\n")

    # SEND TO THINGSPEAK
    send_to_thingspeak(API_A, [Tamb, uviA, distA, Ta, Tw2a, luxA, irA, massA])
    send_to_thingspeak(API_B, [uviB, distB, Tb, Tw2b, massB, luxB, irB, None])
    send_to_thingspeak(API_C, [uviC, distC, Tc, Tw2c, luxC, irC, massC, None])
    send_to_thingspeak(API_W, [wind_speed, wind_dir])

    sleep(PERIOD)

