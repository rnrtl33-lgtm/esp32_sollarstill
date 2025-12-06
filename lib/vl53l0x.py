import time

class VL53L0X:
    def __init__(self, i2c, addr=0x29):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        try:
            self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
            time.sleep_ms(40)
            res = self.i2c.readfrom_mem(self.addr, 0x14, 2)
            return (res[0] << 8) | res[1]
        except:
            return None

