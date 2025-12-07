# ltr390.py — Stable LTR390 driver for ESP32

import time

class LTR390:
    def __init__(self, i2c, addr=0x53):
        self.i2c = i2c
        self.addr = addr
        self.failed = False

        # Initialize safely
        try:
            # Power ON register
            self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
            time.sleep_ms(5)
        except Exception as e:
            print("LTR390 INIT FAILED – USING UV=0 :", e)
            self.failed = True

    def read_uv(self):
        if self.failed:
            return 0

        try:
            data = self.i2c.readfrom_mem(self.addr, 0x07, 3)
            return int.from_bytes(data, "little")
        except:
            return 0



