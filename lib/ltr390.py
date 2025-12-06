import time

LTR390_ADDR = 0x53

class LTR390:
    def __init__(self, i2c, addr=LTR390_ADDR):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x00, b'\x02')  # enable
        self.i2c.writeto_mem(self.addr, 0x07, b'\x0A')  # UV mode

    def read_uv(self):
        d = self.i2c.readfrom_mem(self.addr, 0x10, 3)
        return d[0] | (d[1] << 8) | (d[2] << 16)

    def read_als(self):
        d = self.i2c.readfrom_mem(self.addr, 0x13, 3)
        return d[0] | (d[1] << 8) | (d[2] << 16)

