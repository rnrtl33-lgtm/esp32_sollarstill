import time

class VL53L0X:
    def __init__(self, i2c, address=0x29):
        self.i2c = i2c
        self.address = address
        self._init_sensor()

    def _write(self, reg, val):
        self.i2c.writeto_mem(self.address, reg, bytes([val]))

    def _read(self, reg, n=1):
        return self.i2c.readfrom_mem(self.address, reg, n)

    def _init_sensor(self):
        # Mandatory init (Pololu sequence)
        self._write(0x88, 0x00)
        self._write(0x80, 0x01)
        self._write(0xFF, 0x01)
        self._write(0x00, 0x00)
        self._write(0x91, 0x3C)
        self._write(0x00, 0x01)
        self._write(0xFF, 0x00)
        self._write(0x80, 0x00)

        # Start continuous ranging
        self._write(0x00, 0x02)
        time.sleep_ms(100)

    def read_mm(self, timeout_ms=500):
        start = time.ticks_ms()

        # Wait until data ready OR timeout
        while (self._read(0x13)[0] & 0x07) == 0:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return None
            time.sleep_ms(5)

        data = self._read(0x1E, 2)
        distance = (data[0] << 8) | data[1]

        # Clear interrupt
        self._write(0x0B, 0x01)

        return distance


