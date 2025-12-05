# ============================================================
#                  main.py — Solar Still Project
#      SAFE VERSION + First Reading (No Send) + ThingSpeak
# ============================================================

print("\n=== main.py running ===")
print("Initializing I2C buses...")

import time
from machine import SoftI2C, Pin
import urequests


# ============================================================
#                  THINGSPEAK API KEYS
# ============================================================

API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"

TS_URL = "https://api.thingspeak.com/update"


def send_ts(api_key, fields):
    payload = "api_key=" + api_key
    for i, v in enumerate(fields, 1):
        if v is None:
            v = 0
        payload += "&field{}={}".format(i, v)

    try:
        r = urequests.post(TS_URL, data=payload)
        r.close()
        print("→ TS:", api_key[:6], fields)
    except:
        print("ThingSpeak error")


# ============================================================
#               I2C BUS INITIALIZATION
# ============================================================

i2c_A1 = SoftI2C(sda=Pin(19), scl=Pin(18), freq=100000)
i2c_A2 = SoftI2C(sda=Pin(23), scl=Pin(5), freq=100000)

i2c_B1 = SoftI2C(sda=Pin(25), scl=Pin(26), freq=100000)
i2c_B2 = SoftI2C(sda=Pin(27), scl=Pin(14), freq=100000)

i2c_C1 = SoftI2C(sda=Pin(32), scl=Pin(0), freq=100000)
i2c_C2 = SoftI2C(sda=Pin(15), scl=Pin(2), freq=100000)

print("I2C ready.\n")


# ============================================================
#               ENABLE VL53L0X (XSHUT)
# ============================================================

try:
    Pin(17, Pin.OUT).value(1)
    Pin(22, Pin.OUT).value(1)
    Pin(4,  Pin.OUT).value(1)
except:
    print("XSHUT skipped")

time.sleep_ms(40)


# ============================================================
#               IMPORT SENSOR LIBRARIES
# ============================================================

try:
    from lib.sht30 import SHT30
except:
    print("Missing SHT30")

try:
    from vl53l0x import VL53L0X
except:
    print("Missing VL53L0X")

try:
    import tsl2591
except:
    print("Missing TSL2591")

try:
    from lib.hx711 import HX711
except:
    print("Missing HX711")


# ============================================================
#                     SAFE READ FUNCTIONS
# ============================================================

def safe_sht(s):
    try: return s.measure()
    except: return None, None

def safe_mass(hx):
    try: return hx.get_units(5)
    except: return None

def safe_dist(vl):
    try: return vl.read()
    except: return None

def safe_tsl(t):
    try: return t.read()
    except: return (None, None)

def fmt(v, w=6, p=2):
    if v is None: return "  -- "
    try: return ("{:"+str(w)+"."+str(p)+"f}").format(v)
    except: return "  -- "


# ============================================================
#                   CREATE SENSOR OBJECTS
# ============================================================

print("Creating sensors...")

# --- SHT30 ---
try:
    sht_air_A = SHT30(i2c_A2, addr=0x45)
    sht_w2_A  = SHT30(i2c_A2, addr=0x44)
    sht_amb   = SHT30(i2c_A1, addr=0x44)
except: pass

try:
    sht_air_B = SHT30(i2c_B2, addr=0x45)
    sht_w2_B  = SHT30(i2c_B2, addr=0x44)
except: pass

try:
    sht_air_C = SHT30(i2c_C2, addr=0x45)
    sht_w2_C  = SHT30(i2c_C2, addr=0x44)
except: pass


# --- VL53L0X ---
try: vl_A = VL53L0X(i2c_A1)
except: vl_A = None
try: vl_B = VL53L0X(i2c_B1)
except: vl_B = None
try: vl_C = VL53L0X(i2c_C1)
except: vl_C = None


# --- TSL2591 ---
try: tsl_A = tsl2591.TSL2591(i2c_A2)
except: tsl_A = None
try: tsl_B = tsl2591.TSL2591(i2c_B2)
except: tsl_B = None
try: tsl_C = tsl2591.TSL2591(i2c_C2)
except: tsl_C = None


# --- HX711 ---
try: hxA = HX711(34, 33)
except: hxA = None
try: hxB = HX711(35, 33)
except: hxB = None
try: hxC = HX711(36, 33)
except: hxC = None


# --- WIND (Fake pulses → real speed later) ---
wind_pin = Pin(13, Pin.IN)
wind_count = 0

def wind_irq(p):
    global wind_count
    wind_count += 1

try:
    wind_pin.irq(trigger=Pin.IRQ_FALLING, handler=wind_irq)
except:
    pass

def read_wind():
    global wind_count
    c = wind_count
    wind_count = 0
    return c * 1.2


# ============================================================
#               PRINT FIRST HEADER + FIRST READING
# ============================================================

print("\n==================== SENSOR TABLE ====================")
print("[A] T_air | T_w2 | Tamb | IR | Lux | Dist | Mass")
print("[B] T_air | T_w2 | IR | Lux | Dist | Mass")
print("[C] T_air | T_w2 | IR | Lux | Dist | Mass")
print("[W] Wind Speed")
print("=======================================================\n")


def read_all():
    # ---- A ----
    Ta,_ = safe_sht(sht_air_A)
    Tw2a,_ = safe_sht(sht_w2_A)
    Tamb,_ = safe_sht(sht_amb)
    irA,luxA = safe_tsl(tsl_A)
    distA = safe_dist(vl_A)
    massA = safe_mass(hxA)

    print("[A]", fmt(Ta), fmt(Tw2a), fmt(Tamb),
          fmt(irA), fmt(luxA), fmt(distA,6,0), fmt(massA))

    # ---- B ----
    Tb,_ = safe_sht(sht_air_B)
    Tw2b,_ = safe_sht(sht_w2_B)
    irB,luxB = safe_tsl(tsl_B)
    distB = safe_dist(vl_B)
    massB = safe_mass(hxB)

    print("[B]", fmt(Tb), fmt(Tw2b),
          fmt(irB), fmt(luxB), fmt(distB,6,0), fmt(massB))

    # ---- C ----
    Tc,_ = safe_sht(sht_air_C)
    Tw2c,_ = safe_sht(sht_w2_C)
    irC,luxC = safe_tsl(tsl_C)
    distC = safe_dist(vl_C)
    massC = safe_mass(hxC)

    print("[C]", fmt(Tc), fmt(Tw2c),
          fmt(irC), fmt(luxC), fmt(distC,6,0), fmt(massC))

    # ---- WIND ----
    w = read_wind()
    print("[W] Wind speed:", fmt(w))

    print("-"*60)

    return (Tamb, irA, distA, Ta, Tw2a, luxA, massA), \
           (Tb, Tw2b, irB, luxB, distB, massB), \
           (Tc, Tw2c, irC, luxC, distC, massC), \
           (w, None)


# --------- FIRST READING (NO SEND) ---------
print(">>> First reading (no ThingSpeak send) <<<")
A_vals, B_vals, C_vals, W_vals = read_all()


# ============================================================
#                 MAIN LOOP — SEND EVERY 30 sec
# ============================================================

while True:
    time.sleep(30)

    A_vals, B_vals, C_vals, W_vals = read_all()

    # ------ SEND TO ThingsPeak ------
    send_ts(API_A, A_vals)
    send_ts(API_B, B_vals)
    send_ts(API_C, C_vals)
    send_ts(API_W, W_vals)




