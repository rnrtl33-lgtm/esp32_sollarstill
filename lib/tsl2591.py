import time

TSL = 0x29

class TSL2591:
    ENABLE = 0x00
    CONTROL = 0x01
    CH0 = 0x14
    CH1 = 0x16

    def __init__(self, i2c, addr=TSL):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, self.ENABLE, b'\x03')
        self.i2c.writeto_mem(self.addr, self.CONTROL, b'\x20')

    def read(self):
        d0 = self.i2c.readfrom_mem(self.addr, self.CH0, 2)
        d1 = self.i2c.readfrom_mem(self.addr, self.CH1, 2)
        ch0 = d0[0] | (d0[1] << 8)
        ch1 = d1[0] | (d1[1] << 8)
        return ch0, ch1

