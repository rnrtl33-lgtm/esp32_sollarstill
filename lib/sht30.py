# MicroPython SHT30 Driver
import time

class SHT30:
    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        self.i2c.writeto(self.addr, b'\x2C\x06')
        time.sleep(0.015)
        data = self.i2c.readfrom(self.addr, 6)

        temp_raw = data[0] << 8 | data[1]
        hum_raw = data[3] << 8 | data[4]

        temp = -45 + (175 * (temp_raw / 65535))
        hum = 100 * (hum_raw / 65535)

        return temp, hum

