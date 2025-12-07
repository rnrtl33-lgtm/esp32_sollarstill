# LTR390 MicroPython Driver (Stable Version)
# Works with Device ID = 0xB2

import time

class LTR390:
    LTR390_ADDR = 0x53

    REG_MAIN_CTRL = 0x00
    REG_PART_ID = 0x06
    REG_MEAS_RATE = 0x04
    REG_GAIN = 0x05

    REG_UVS_DATA_0 = 0x10   # UV
    REG_ALS_DATA_0 = 0x0D   # ALS (light)

    MODE_ALS = 0x00
    MODE_UVS = 0x02

    def __init__(self, i2c, addr=0x53):
        self.i2c = i2c
        self.addr = addr

        # Check device ID — optional but safe
        try:
            part_id = self.i2c.readfrom_mem(self.addr, self.REG_PART_ID, 1)[0]
            # No strict check because many revisions exist (0xB2, 0x00, 0x05)
        except:
            raise OSError("LTR390 not responding")

        # Enable sensor (ALS mode initially)
        self._write(self.REG_MAIN_CTRL, 0x0A)  # Enable + ALS mode
        time.sleep(0.1)

        # Set measurement rate & resolution
        self._write(self.REG_MEAS_RATE, 0x22)

        # Set gain
        self._write(self.REG_GAIN, 0x02)

    def _write(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    def _read3(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 3)
        return data[0] | (data[1] << 8) | (data[2] << 16)

    def read_uv(self):
        # UV mode
        self._write(self.REG_MAIN_CTRL, 0x0A | self.MODE_UVS)
        time.sleep(0.1)
        raw = self._read3(self.REG_UVS_DATA_0)
        return raw

    def read_lux(self):
        # ALS mode
        self._write(self.REG_MAIN_CTRL, 0x0A | self.MODE_ALS)
        time.sleep(0.1)
        raw = self._read3(self.REG_ALS_DATA_0)
        return raw


