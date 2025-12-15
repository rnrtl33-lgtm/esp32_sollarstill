from machine import Pin
import time

class HX711:
    def __init__(self, dout, sck, gain=128):
        self.dout = Pin(dout, Pin.IN, pull=None)
        self.sck = Pin(sck, Pin.OUT)
        self.gain = gain

        # Set gain
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2
        else:
            self.GAIN = 1

        self.offset = 0
        self.scale = 1

    def is_ready(self):
        return self.dout.value() == 0

    def read_raw(self):
        while not self.is_ready():
            time.sleep_ms(1)

        data = 0
        for _ in range(24):
            self.sck.value(1)
            data = (data << 1) | self.dout.value()
            self.sck.value(0)

        # Set gain for next read
        for _ in range(self.GAIN):
            self.sck.value(1)
            self.sck.value(0)

        # Convert to signed number
        if data & 0x800000:
            data |= ~0xFFFFFF

        return data

    def read(self, samples=10):
        total = 0
        for _ in range(samples):
            total += self.read_raw()
        return total / samples

    def tare(self, samples=15):
        self.offset = self.read(samples)

    def set_scale(self, scale):
        self.scale = scale

    def get_weight(self, samples=10):
        value = self.read(samples)
        value = value - self.offset
        return value / self.scale
