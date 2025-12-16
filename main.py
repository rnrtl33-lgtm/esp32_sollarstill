from machine import Pin, SoftI2C
import time
import machine
import urequests


START_TIME = time.time()
RESTART_INTERVAL = 300     
SEND_INTERVAL = 20         
last_send = 0



# Model A
i2c_A1 = SoftI2C(scl=Pin(18), sda=Pin(19), freq=100000)
i2c_A2 = SoftI2C(scl=Pin(5),  sda=Pin(23), freq=100000)

# Model B
i2c_B1 = SoftI2C(scl=Pin(26), sda=Pin(25), freq=100000)
i2c_B2 = SoftI2C(scl=Pin(14), sda=Pin(27), freq=100000)

# Model C
i2c_C1 = SoftI2C(scl=Pin(0),  sda=Pin(32), freq=100000)
i2c_C2 = SoftI2C(scl=Pin(2),  sda=Pin(15), freq=100000)


from ltr390_clean import LTR390
from tsl2591_clean import TSL2591

ltr_A = LTR390(i2c_A1)
ltr_B = LTR390(i2c_B1)
ltr_C = LTR390(i2c_C1)

tsl_A = TSL2591(i2c_A2)
tsl_B = TSL2591(i2c_B2)
tsl_C = TSL2591(i2c_C2)

for tsl in (tsl_A, tsl_B, tsl_C):
    tsl.gain = tsl.GAIN_MED
    tsl.integration_time = tsl.INTEGRATIONTIME_300MS


ADDR_TOF = 0x29

def read_distance(i2c):
    try:
        i2c.writeto_mem(ADDR_TOF, 0x00, b'\x01')
        time.sleep_ms(60)
        data = i2c.readfrom_mem(ADDR_TOF, 0x14, 12)
        d = (data[10] << 8) | data[11]
        return None if d >= 8190 else d
    except:
        return None

def read_sht30(i2c, addr):
    try:
        i2c.writeto(addr, b'\x2C\x06')
        time.sleep_ms(20)
        data = i2c.readfrom(addr, 6)
        t = -45 + (175 * ((data[0] << 8) | data[1]) / 65535)
        h = 100 * (((data[3] << 8) | data[4]) / 65535)
        return round(t, 2), round(h, 2)
    except:
        return None, None

def read_ltr(ltr):
    try:
        ltr.set_als_mode()
        als = ltr.read_als()
        ltr.set_uvs_mode()
        uv = ltr.read_uv()
        return als, uv
    except:
        return None, None

def read_tsl(tsl):
    try:
        full, ir = tsl.get_raw_luminosity()
        lux = tsl.calculate_lux(full, ir)
        return ir, round(lux, 2)
    except:
        return None, None

def send_thingspeak(api_key, fields):
    payload = {"api_key": api_key}
    for k, v in fields.items():
        if v is not None:
            payload[k] = v
    try:
        r = urequests.post("https://api.thingspeak.com/update", json=payload)
        r.close()
    except:
        pass


# Main Loop

while True:

  
    als_A, uv_A = read_ltr(ltr_A)
    ir_A, lux_A = read_tsl(tsl_A)
    d_A = read_distance(i2c_A1)
    tA_amb, hA_amb = read_sht30(i2c_A1, 0x45)
    tA_air, hA_air = read_sht30(i2c_A2, 0x44)
    tA_wat, hA_wat = read_sht30(i2c_A2, 0x45)

    
    als_B, uv_B = read_ltr(ltr_B)
    ir_B, lux_B = read_tsl(tsl_B)
    d_B = read_distance(i2c_B1)
    tB_air, hB_air = read_sht30(i2c_B2, 0x44)
    tB_wat, hB_wat = read_sht30(i2c_B2, 0x45)

    
    als_C, uv_C = read_ltr(ltr_C)
    ir_C, lux_C = read_tsl(tsl_C)
    d_C = read_distance(i2c_C1)
    tC_air, hC_air = read_sht30(i2c_C2, 0x44)
    tC_wat, hC_wat = read_sht30(i2c_C2, 0x45)

    
    if time.time() - last_send > SEND_INTERVAL:

        # Model A
        send_thingspeak(
            "EU6EE36IJ7WSVYP3",
            {
                "field1": tA_amb,
                "field2": als_A,
                "field3": d_A,
                "field4": tA_air,
                "field5": tA_wat,
                "field6": lux_A,
                "field7": ir_A,
            }
        )

        # Model B
        send_thingspeak(
            "E8CTAK8MCUWLQJ2",
            {
                "field1": uv_B,
                "field2": d_B,
                "field3": tB_air,
                "field4": tB_wat,
                "field6": lux_B,
                "field7": ir_B,
            }
        )

        # Model C
        send_thingspeak(
            "Y1FWSOX7Z6YZ8QMU",
            {
                "field1": uv_C,
                "field2": d_C,
                "field3": tC_air,
                "field4": tC_wat,
                "field5": lux_C,
                "field6": ir_C,
            }
        )

        last_send = time.time()

   
    if time.time() - START_TIME > RESTART_INTERVAL:
        print("Restarting for OTA update")
        time.sleep(2)
        machine.reset()

    time.sleep(1)
