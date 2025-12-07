import time

class VL53L0X:
    def __init__(self, i2c, addr=0x29):
        self.i2c = i2c
        self.addr = addr
        self._init_sensor()

    def _init_sensor(self):
        # Basic init sequence
        try:
            self.i2c.writeto_mem(self.addr, 0x88, b'\x00')
        except:
            pass

    # -----------------------------
    # Added to support main.py logic
    # -----------------------------
    def start(self):
        """
        Dummy start method for compatibility.
        The sensor initializes automatically in read().
        """
        try:
            # Put sensor in single-shot ranging mode
            self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
        except:
            pass

    # -----------------------------
    # Main distance read function
    # -----------------------------
    def read(self):
        # Trigger single measurement
        self.i2c.writeto_mem(self.addr, 0x00, b'\x01')
        time.sleep_ms(50)

        # Read distance result
        res = self.i2c.readfrom_mem(self.addr, 0x14, 2)
        return (res[0] << 8) | res[1]


