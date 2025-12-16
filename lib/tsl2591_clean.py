import time

TSL2591_ADDR = 0x29

COMMAND_BIT = 0xA0
ENABLE_REGISTER = 0x00
CONTROL_REGISTER = 0x01
CH0_LOW = 0x14
CH1_LOW = 0x16

ENABLE_POWERON = 0x01
ENABLE_AEN = 0x02


class TSL2591:
    GAIN_LOW = 0x00
    GAIN_MED = 0x10
    GAIN_HIGH = 0x20
    GAIN_MAX = 0x30

    INTEGRATIONTIME_100MS = 0x00
    INTEGRATIONTIME_200MS = 0x01
    INTEGRATIONTIME_300MS = 0x02
    INTEGRATIONTIME_400MS = 0x03
    INTEGRATIONTIME_500MS = 0x04
    INTEGRATIONTIME_600MS = 0x05

    def __init__(self, i2c):
        self.i2c = i2c
        self.address = TSL2591_ADDR
        self.gain = self.GAIN_MED
        self.integration_time = self.INTEGRATIONTIME_300MS
        self.enable()

    def write_register(self, reg, value):
        self.i2c.writeto_mem(self.address, COMMAND_BIT | reg, bytes([value]))

    def read_register(self, reg, length=1):
        return self.i2c.readfrom_mem(self.address, COMMAND_BIT | reg, length)

    def enable(self):
        self.write_register(ENABLE_REGISTER, ENABLE_POWERON | ENABLE_AEN)
        time.sleep_ms(10)
        self.set_timing()

    def set_timing(self):
        self.write_register(CONTROL_REGISTER, self.gain | self.integration_time)
        time.sleep_ms(10)

    def get_raw_luminosity(self):
        ch0 = self.read_register(CH0_LOW, 2)
        ch1 = self.read_register(CH1_LOW, 2)

        full = (ch0[1] << 8) | ch0[0]
        ir = (ch1[1] << 8) | ch1[0]

        return full, ir

    def calculate_lux(self, full, ir):
        if full == 0:
            return 0

        visible = full - ir
        if visible < 0:
            visible = 0

        atime = (self.integration_time + 1) * 100
        again = {
            self.GAIN_LOW: 1,
            self.GAIN_MED: 25,
            self.GAIN_HIGH: 428,
            self.GAIN_MAX: 9876
        }[self.gain]

        cpl = (atime * again) / 408.0
        return visible / cpl
