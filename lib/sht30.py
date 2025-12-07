import time

class SHT30:
    def __init__(self, i2c, address=0x44):
        self.i2c = i2c
        self.addr = address

    def measure(self):
        # Send measurement command
        self.i2c.writeto(self.addr, b'\x2C\x06')
        time.sleep_ms(15)

        data = self.i2c.readfrom(self.addr, 6)
        if len(data) != 6:
            return None, None

        t_raw = data[0] << 8 | data[1]
        h_raw = data[3] << 8 | data[4]

        temp = -45 + (175 * (t_raw / 65535))
        hum  = 100 * (h_raw / 65535)

        return round(temp, 2), round(hum, 2)
