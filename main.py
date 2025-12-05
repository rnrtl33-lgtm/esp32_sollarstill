# ============================================================
#                main.py — FULL SAFE TEST VERSION
#         Reads A + B + C + Wind, prints formatted table
# ============================================================

print("\n=== main.py running ===")
print("Initializing I2C buses...")

import time
from machine import SoftI2C, Pin

# ========== CREATE I2C BUSES ==========
i2c_A1 = SoftI2C(sda=Pin(19), scl=Pin(18), freq=100000)
i2c_A2 = SoftI2C(sda=Pin(23), scl=Pin(5), freq=100000)

i2c_B1 = SoftI2C(sda=Pin(25), scl=Pin(26), freq=100000)
i2c_B2 = SoftI2C(sda=Pin(27), scl=Pin(14), freq=100000)

i2c_C1 = SoftI2C(sda=Pin(32), scl=Pin(0), freq=100000)
i2c_C2 = SoftI2C(sda=Pin(15), scl=Pin(2), freq=100000)

print("I2C ready.\n")


# ============================================================
#                    ENABLE XSHUT (VL53L0X)
# ============================================================

try:
    xA = Pin(17, Pin.OUT); xA.value(1)
    xB = Pin(22, Pin.OUT); xB.value(1)
    xC = Pin(4,  Pin.OUT); xC.value(1)
except:
    print("XSHUT pins skipped.")

time.sleep_ms(30)


# ============================================================
#             IMPORT LIBRARIES (SAFE IMPORT)
# ============================================================

try:
    from lib.sht30 import SHT30
except:
    print("SHT30 LIB MISSING")

try:
    from vl53l0x import VL53L0X
except:
    print("VL53L0X LIB MISSING")

try:
    import tsl2591
except:
    print("TSL2591 LIB MISSING")

try:
    from lib.hx711 import HX711
except:
    print("HX711 LIB MISSING")


# ============================================================
#          SAFE FUNCTIONS — NEVER CRASH
# ============================================================

def safe_sht(sensor):
    try:
        return sensor.measure()
    except:
        return None, None

def safe_mass(hx):
    try:
        return hx.get_units(5)
    except:
        return None

def safe_dist(vl):
    try:
        return vl.read()
    except:
        return None

def safe_uv(uv_func):
    try:
        return uv_func()
    except:
        return None, None

def safe_tsl(tsl):
    try:
        ir, lux = tsl.read()
        return ir, lux
    except:
        return None, None


def fmt(v, w=6, p=2):
    if v is None:
        return "  -- "
    try:
        return ("{:"+str(w)+"."+str(p)+"f}").format(v)
    except:
        return "  -- "


# ============================================================
#               INSTANTIATE ALL SENSORS
# ============================================================

print("Creating sensors...")

# ---------- SHT30 ----------
try:
    sht_air_A = SHT30(i2c_A2, addr=0x45)
    sht_w2_A  = SHT30(i2c_A2, addr=0x44)
    sht_amb   = SHT30(i2c_A1, addr=0x44)
except:
    print("Error SHT30 A")

try:
    sht_air_B = SHT30(i2c_B2, addr=0x45)
    sht_w2_B  = SHT30(i2c_B2, addr=0x44)
except:
    print("Error SHT30 B")

try:
    sht_air_C = SHT30(i2c_C2, addr=0x45)
    sht_w2_C  = SHT30(i2c_C2, addr=0x44)
except:
    print("Error SHT30 C")


# ---------- VL53L0X ----------
try:
    vl_A = VL53L0X(i2c_A1)
except:
    vl_A = None

try:
    vl_B = VL53L0X(i2c_B1)
except:
    vl_B = None

try:
    vl_C = VL53L0X(i2c_C1)
except:
    vl_C = None


# ---------- TSL2591 ----------
try:
    tsl_A = tsl2591.TSL2591(i2c_A2)
except:
    tsl_A = None

try:
    tsl_B = tsl2591.TSL2591(i2c_B2)
except:
    tsl_B = None

try:
    tsl_C = tsl2591.TSL2591(i2c_C2)
except:
    tsl_C = None


# ---------- HX711 ----------
try:
    hxA = HX711(34, 33)
except:
    hxA = None

try:
    hxB = HX711(35, 33)
except:
    hxB = None

try:
    hxC = HX711(36, 33)
except:
    hxC = None


# ---------- WIND ----------
wind_pin = Pin(13, Pin.IN)
wind_count = 0

def wind_irq(pin):
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
    return c * 1.2   # fake scaling


# ============================================================
#                  PRINT TABLE HEADER
# ============================================================

print("\n==================== SENSOR TABLE ====================")
print("[A] T_air | T_w2 | Tamb | UV | UVI | IR | Lux | Dist | Mass")
print("[B] T_air | T_w2 | UV | UVI | IR | Lux | Dist | Mass")
print("[C] T_air | T_w2 | UV | UVI | IR | Lux | Dist | Mass")
print("[W] Wind Speed")
print("=======================================================\n")

# ============================================================
#                      MAIN LOOP
# ============================================================

while True:

    # ------ Model A ------
    Ta, _   = safe_sht(sht_air_A)
    Tw2a,_  = safe_sht(sht_w2_A)
    Tamb,_  = safe_sht(sht_amb)
    distA   = safe_dist(vl_A)
    massA   = safe_mass(hxA)
    irA,luxA = safe_tsl(tsl_A)
    uvA, uviA = None, None   # LTR390 removed here unless added

    print("[A]", fmt(Ta), fmt(Tw2a), fmt(Tamb), fmt(uvA), fmt(uviA),
          fmt(irA), fmt(luxA), fmt(distA,6,0), fmt(massA))

    # ------ Model B ------
    Tb,_    = safe_sht(sht_air_B)
    Tw2b,_  = safe_sht(sht_w2_B)
    distB   = safe_dist(vl_B)
    massB   = safe_mass(hxB)
    irB,luxB = safe_tsl(tsl_B)

    print("[B]", fmt(Tb), fmt(Tw2b), "   -- ", "   -- ", 
          fmt(irB), fmt(luxB), fmt(distB,6,0), fmt(massB))

    # ------ Model C ------
    Tc,_    = safe_sht(sht_air_C)
    Tw2c,_  = safe_sht(sht_w2_C)
    distC   = safe_dist(vl_C)
    massC   = safe_mass(hxC)
    irC,luxC = safe_tsl(tsl_C)

    print("[C]", fmt(Tc), fmt(Tw2c), "   -- ", "   -- ",
          fmt(irC), fmt(luxC), fmt(distC,6,0), fmt(massC))

    # ------ WIND ------
    w = read_wind()
    print("[W] Wind speed:", fmt(w))

    print("-" * 50)
    time.sleep(30)
# ============================================================
#                     MAIN LOOP (FAST FIRST PRINT)
# ============================================================

def read_all_once():
    # ------ Model A ------
    Ta,_    = safe_sht(sht_air_A)
    Tw2a,_  = safe_sht(sht_w2_A)
    Tamb,_  = safe_sht(sht_amb)
    distA   = safe_dist(vl_A)
    massA   = safe_mass(hxA)
    irA,luxA = safe_tsl(tsl_A)
    uvA,uviA = None, None

    print("[A]", fmt(Ta), fmt(Tw2a), fmt(Tamb), fmt(uvA), fmt(uviA),
          fmt(irA), fmt(luxA), fmt(distA,6,0), fmt(massA))

    # ------ Model B ------
    Tb,_    = safe_sht(sht_air_B)
    Tw2b,_  = safe_sht(sht_w2_B)
    distB   = safe_dist(vl_B)
    massB   = safe_mass(hxB)
    irB,luxB = safe_tsl(tsl_B)

    print("[B]", fmt(Tb), fmt(Tw2b), "   -- ", "   -- ",
          fmt(irB), fmt(luxB), fmt(distB,6,0), fmt(massB))

    # ------ Model C ------
    Tc,_    = safe_sht(sht_air_C)
    Tw2c,_  = safe_sht(sht_w2_C)
    distC   = safe_dist(vl_C)
    massC   = safe_mass(hxC)
    irC,luxC = safe_tsl(tsl_C)

    print("[C]", fmt(Tc), fmt(Tw2c), "   -- ", "   -- ",
          fmt(irC), fmt(luxC), fmt(distC,6,0), fmt(massC))

    # ------ WIND ------
    w = read_wind()
    print("[W] Wind speed:", fmt(w))

    print("-"*50)


# ----------- PRINT FIRST READING IMMEDIATELY -----------
print("\n>>> FIRST READING (no delay) <<<")
read_all_once()

# ----------- THEN LOOP EVERY 30 SECONDS -----------
while True:
    time.sleep(30)
    read_all_once()



    print("Running main.py loop...")
    time.sleep(5)


