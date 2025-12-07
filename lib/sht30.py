# sht30.py — Fully custom driver for SHT30 with address support

import time

class SHT30:

    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def _write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([cmd >> 8, cmd & 0xFF]))

    def measure(self):
        # Single shot mode (high repeatability)
        self._write_cmd(0x2400)
        time.sleep_ms(15)

        data = self.i2c.readfrom(self.addr, 6)

        t_raw = data[0] << 8 | data[1]
        h_raw = data[3] << 8 | data[4]

        temp = -45 + (175 * (t_raw / 65535.0))
        hum = 100 * (h_raw / 65535.0)

        return round(temp, 2), round(hum, 2)
