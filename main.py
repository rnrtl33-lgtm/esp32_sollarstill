
import time, gc, socket
from machine import Pin, SoftI2C, reset

 
from ltr390_clean import LTR390
from tsl2591_clean import TSL2591


API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLQJ2"
API_C = "Y1FWSOX7Z6YZ8QMU"
# API_D


def http_get(url):
    try:
        proto, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        s.send(b"GET /" + path.encode() +
               b" HTTP/1.0\r\nHost:" +
               host.encode() + b"\r\n\r\n")
        data = b""
        while True:
            part = s.recv(256)
            if not part:
                break
            data += part
        s.close()
        return data.split(b"\r\n\r\n", 1)[1].decode()
    except:
        return None


# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19))
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23))

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25))
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27))

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32))
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15))


ADDR_TOF = 0x29

def read_distance(i2c):
    try:
        i2c.writeto_mem(ADDR_TOF, 0x00, b"\x01")
        time.sleep_ms(60)
        data = i2c.readfrom_mem(ADDR_TOF, 0x14, 12)
        d = (data[10] << 8) | data[11]
        return None if d >= 8190 else d
    except:
        return None

def read_sht30(i2c, addr):
    try:
        i2c.writeto(addr, b"\x2C\x06")
        time.sleep_ms(20)
        data = i2c.readfrom(addr, 6)
        t = -45 + (175 * ((data[0] << 8) | data[1]) / 65535)
        h = 100 * (((data[3] << 8) | data[4]) / 65535)
        return round(t,2), round(h,2)
    except:
        return None, None


def init_A():
    return {
        "ltr": LTR390(i2c_A1),
        "tsl": TSL2591(i2c_A2)
    }

def init_B():
    return {
        "ltr": LTR390(i2c_B1),
        "tsl": TSL2591(i2c_B2)
    }

def init_C():
    return {
        "ltr": LTR390(i2c_C1),
        "tsl": TSL2591(i2c_C2)
    }

sA = init_A()
sB = init_B()
sC = init_C()

for s in (sA, sB, sC):
    s["tsl"].gain = s["tsl"].GAIN_MED
    s["tsl"].integration_time = s["tsl"].INTEGRATIONTIME_300MS


def read_A():
    t_amb, h_amb = read_sht30(i2c_A1, 0x45)
    t_air, h_air = read_sht30(i2c_A2, 0x44)
    t_wat, h_wat = read_sht30(i2c_A2, 0x45)

    sA["ltr"].set_als_mode()
    als = sA["ltr"].read_als()
    sA["ltr"].set_uvs_mode()
    uv = sA["ltr"].read_uv()

    full, ir = sA["tsl"].get_raw_luminosity()
    lux = sA["tsl"].calculate_lux(full, ir)

    return {
        "ambient": t_amb,
        "air": t_air,
        "water": t_wat,
        "uv": uv,
        "distance": read_distance(i2c_A1),
        "lux": round(lux,2),
        "ir": ir
    }

def read_B():
    t_air, h_air = read_sht30(i2c_B2, 0x44)
    t_wat, h_wat = read_sht30(i2c_B2, 0x45)

    sB["ltr"].set_uvs_mode()
    uv = sB["ltr"].read_uv()

    full, ir = sB["tsl"].get_raw_luminosity()
    lux = sB["tsl"].calculate_lux(full, ir)

    return {
        "uv": uv,
        "distance": read_distance(i2c_B1),
        "air": t_air,
        "water": t_wat,
        "lux": round(lux,2),
        "ir": ir
    }

def read_C():
    t_air, h_air = read_sht30(i2c_C2, 0x44)
    t_wat, h_wat = read_sht30(i2c_C2, 0x45)

    sC["ltr"].set_uvs_mode()
    uv = sC["ltr"].read_uv()

    full, ir = sC["tsl"].get_raw_luminosity()
    lux = sC["tsl"].calculate_lux(full, ir)

    return {
        "uv": uv,
        "distance": read_distance(i2c_C1),
        "air": t_air,
        "water": t_wat,
        "lux": round(lux,2),
        "ir": ir
    }


def send_ts(key, data):
    url = "http://api.thingspeak.com/update?api_key=" + key
    i = 1
    for v in data.values():
        url += "&field{}={}".format(i, v)
        i += 1
    http_get(url)


print("\n>>> Unified A+B+C running (Auto-Restart OTA) <<<\n")

cycle = 0

while True:
    A = read_A()
    B = read_B()
    C = read_C()

    print("A:", A)
    print("B:", B)
    print("C:", C)

    send_ts(API_A, A)
    send_ts(API_B, B)
    send_ts(API_C, C)

    gc.collect()

    cycle += 1
    if cycle >= 15:   
        print("Auto-restart for OTA update…")
        time.sleep(1)
        reset()

    time.sleep(20)
