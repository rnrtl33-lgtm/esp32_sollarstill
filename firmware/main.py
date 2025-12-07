import network
import urequests
import time
from machine import I2C, SoftI2C, Pin

# ==========================
#  WiFi CONFIG
# ==========================
WIFI_SSID = "Abdullah's phone"
WIFI_PASS = "42012999"

# ==========================
#  THINGSPEAK API KEYS
# ==========================
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
API_W = "HG8GG8DF40LCGV99"

# ==========================
#  I2C BUS DEFINITIONS
# ==========================
# A: Bus0
i2c_A1 = I2C(0, scl=Pin(18), sda=Pin(19))
i2c_A2 = I2C(1, scl=Pin(5),  sda=Pin(23))

# B: Bus1
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(32), sda=Pin(33))

# C: Bus2
i2c_C1 = SoftI2C(scl=Pin(14), sda=Pin(27))
i2c_C2 = SoftI2C(scl=Pin(4),  sda=Pin(15))

# ==========================
#  WIND SENSOR
# ==========================
wind_pin = Pin(13, Pin.IN)
wind_count = 0

def wind_irq(p):
    global wind_count
    wind_count += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)

def read_wind_speed():
    """ يحسب نبضات الرياح خلال 3 ثواني """
    global wind_count
    wind_count = 0
    time.sleep(3)
    speed = wind_count * 0.2  # تحويل تقريبي
    return speed

# ==========================
#  SENSOR SAFE READ
# ==========================
def safe_read(func, fallback=0):
    try:
        return func()
    except:
        return fallback

# ==========================
#  IMPORT SENSOR LIBRARIES
# ==========================
from lib.sht30 import SHT30
from lib.vl53l0x import VL53L0X
from lib.ltr390 import LTR390
from lib.tsl2591 import TSL2591
from lib.hx711 import HX711

# ==========================
#  INIT SENSORS
# ==========================
def init_all():

    # MODEL A
    A = {}
    A["amb"]  = SHT30(i2c_A1)
    A["uv"]   = LTR390(i2c_A1)
    A["dist"] = VL53L0X(i2c_A1)
    A["air"]  = SHT30(i2c_A2)
    A["w2"]   = SHT30(i2c_A2)
    A["lux"]  = TSL2591(i2c_A1)
    A["hx"]   = HX711(d_out=21, pd_sck=22)

    # MODEL B
    B = {}
    B["uv"]   = LTR390(i2c_B1)
    B["dist"] = VL53L0X(i2c_B1)
    B["air"]  = SHT30(i2c_B2)
    B["w2"]   = SHT30(i2c_B2)
    B["lux"]  = TSL2591(i2c_B1)
    B["hx"]   = HX711(d_out=17, pd_sck=16)

    # MODEL C
    C = {}
    C["uv"]   = LTR390(i2c_C1)
    C["dist"] = VL53L0X(i2c_C1)
    C["air"]  = SHT30(i2c_C2)
    C["w2"]   = SHT30(i2c_C2)
    C["lux"]  = TSL2591(i2c_C1)
    C["hx"]   = HX711(d_out=2, pd_sck=0)

    return A, B, C

A, B, C = init_all()

# ==========================
#  WIFI CONNECT
# ==========================
def wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(WIFI_SSID, WIFI_PASS)

    while not sta.isconnected():
        print("Connecting WiFi...")
        time.sleep(1)

    print("WiFi:", sta.ifconfig())
    return True

wifi()

# ==========================
#  SEND TO THINGSPEAK
# ==========================
def send_ts(api, **fields):
    url = "https://api.thingspeak.com/update?api_key=" + api
    for k, v in fields.items():
        url += f"&{k}={v}"
    try:
        r = urequests.get(url)
        r.close()
    except:
        pass

# ==========================
#  MAIN LOOP
# ==========================
print("MAIN STARTED")

while True:

    print("\nReading sensors...")

    # ------------------------------
    # MODEL A
    # ------------------------------
    A_amb = safe_read(lambda: A["amb"].read())
    A_uv  = safe_read(lambda: A["uv"].read_uv())
    A_dis = safe_read(lambda: A["dist"].read())
    A_air = safe_read(lambda: A["air"].read())
    A_w2  = safe_read(lambda: A["w2"].read())
    A_lux = safe_read(lambda: A["lux"].lux())
    A_ir  = safe_read(lambda: A["lux"].ir())
    A_hx  = safe_read(lambda: A["hx"].read())

    send_ts(API_A,
        field1=A_amb[0] if A_amb else 0,
        field2=A_uv,
        field3=A_dis,
        field4=A_air[0] if A_air else 0,
        field5=A_w2[0] if A_w2 else 0,
        field6=A_lux,
        field7=A_ir,
        field8=A_hx
    )

    # ------------------------------
    # MODEL B
    # ------------------------------
    B_uv  = safe_read(lambda: B["uv"].read_uv())
    B_dis = safe_read(lambda: B["dist"].read())
    B_air = safe_read(lambda: B["air"].read())
    B_w2  = safe_read(lambda: B["w2"].read())
    B_lux = safe_read(lambda: B["lux"].lux())
    B_ir  = safe_read(lambda: B["lux"].ir())
    B_hx  = safe_read(lambda: B["hx"].read())

    send_ts(API_B,
        field1=B_uv,
        field2=B_dis,
        field3=B_air[0] if B_air else 0,
        field4=B_w2[0] if B_w2 else 0,
        field5=B_hx,
        field6=B_lux,
        field7=B_ir
    )

    # ------------------------------
    # MODEL C
    # ------------------------------
    C_uv  = safe_read(lambda: C["uv"].read_uv())
    C_dis = safe_read(lambda: C["dist"].read())
    C_air = safe_read(lambda: C["air"].read())
    C_w2  = safe_read(lambda: C["w2"].read())
    C_lux = safe_read(lambda: C["lux"].lux())
    C_ir  = safe_read(lambda: C["lux"].ir())
    C_hx  = safe_read(lambda: C["hx"].read())

    send_ts(API_C,
        field1=C_uv,
        field2=C_dis,
        field3=C_air[0] if C_air else 0,
        field4=C_w2[0] if C_w2 else 0,
        field5=C_lux,
        field6=C_ir,
        field7=C_hx
    )

    # ------------------------------
    # WIND
    # ------------------------------
    w = read_wind_speed()

    send_ts(API_W,
        field1=w
    )

    print("TS:", time.ticks_ms()//1000)
    time.sleep(15)   # إرسال كل 15 ثانية









   


