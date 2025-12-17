import time, socket, gc
from machine import Pin, SoftI2C, reset


from lib.sht30_clean import SHT30
from lib.ltr390_fixed import LTR390
from lib.tsl2591_fixed import TSL2591
from lib.vl53l0x_clean import VL53L0X
from lib.hx711_simple import HX711


TS_A = "EU6EE36IJ7WSVYP3"
TS_B = "E8CTAK8MCUWLVQJ2"
TS_C = "Y1FWSOX7Z6YZ8QMU"
TS_D = "HG8G8DF40LCGV99"


def ts_send(key, data):
    url = "http://api.thingspeak.com/update?api_key=" + key
    i = 1
    for v in data:
        url += "&field{}={}".format(i, v)
        i += 1

    try:
        addr = socket.getaddrinfo("api.thingspeak.com", 80)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(b"GET " + url.split("http://api.thingspeak.com")[1].encode() + b" HTTP/1.0\r\nHost: api.thingspeak.com\r\n\r\n")
        s.close()
    except:
        pass


i2cA1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2cA2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

i2cB1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2cB2 = SoftI2C(scl=Pin(14), sda=Pin(27))

i2cC1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2cC2 = SoftI2C(scl=Pin(2),  sda=Pin(15))


hxA = HX711(dt=34, sck=33)
hxB = HX711(dt=35, sck=33)
hxC = HX711(dt=36, sck=33)


wind_pin = Pin(4, Pin.IN)
wind_pulses = 0

def wind_irq(p):
    global wind_pulses
    wind_pulses += 1

wind_pin.irq(trigger=Pin.IRQ_RISING, handler=wind_irq)


A = {
    "amb": SHT30(i2cA1, 0x45),
    "air": SHT30(i2cA2, 0x45),
    "wat": SHT30(i2cA2, 0x44),
    "uv":  LTR390(i2cA1),
    "lux": TSL2591(i2cA2),
    "dis": VL53L0X(i2cA1),
}

B = {
    "air": SHT30(i2cB2, 0x45),
    "wat": SHT30(i2cB2, 0x44),
    "uv":  LTR390(i2cB1),
    "lux": TSL2591(i2cB2),
    "dis": VL53L0X(i2cB1),
}

C = {
    "air": SHT30(i2cC2, 0x45),
    "wat": SHT30(i2cC2, 0x44),
    "uv":  LTR390(i2cC1),
    "lux": TSL2591(i2cC2),
}

print("\n>>> SYSTEM RUNNING (A+B+C+D) <<<\n")

cycle = 0

while True:
    
    Ta, Ha = A["amb"].measure()
    Tair, Hair = A["air"].measure()
    Tw, Hw = A["wat"].measure()
    alsA = A["uv"].read_als()
    uvA  = A["uv"].read_uv()
    full, ir = A["lux"].get_raw_luminosity()
    luxA = A["lux"].calculate_lux(full, ir)
    distA = A["dis"].read()
    wA = hxA.get_weight()

    ts_send(TS_A, [Ta, alsA, distA, Tair, Tw, luxA, ir, wA])

   
    TairB, HairB = B["air"].measure()
    TwB, HwB = B["wat"].measure()
    alsB = B["uv"].read_als()
    uvB  = B["uv"].read_uv()
    fullB, irB = B["lux"].get_raw_luminosity()
    luxB = B["lux"].calculate_lux(fullB, irB)
    distB = B["dis"].read()
    wB = hxB.get_weight()

    ts_send(TS_B, [uvB, distB, TairB, TwB, wB, luxB, irB])

   
    TairC, HairC = C["air"].measure()
    TwC, HwC = C["wat"].measure()
    alsC = C["uv"].read_als()
    uvC  = C["uv"].read_uv()
    fullC, irC = C["lux"].get_raw_luminosity()
    luxC = C["lux"].calculate_lux(fullC, irC)
    wC = hxC.get_weight()

    ts_send(TS_C, [uvC, None, TairC, TwC, luxC, irC, wC])

    
    p = wind_pulses
    wind_pulses = 0
    wind_speed = (p / 2) * 0.4
    ts_send(TS_D, [wind_speed])

    print("Cycle:", cycle)
    cycle += 1

    if cycle >= 15:  
        print("Auto reset for OTA")
        time.sleep(2)
        reset()

    gc.collect()
    time.sleep(20)
