from machine import Pin
import time

class HX711:
    def __init__(self, dout, sck, gain=128, timeout_ms=1000):
        self.dout = Pin(dout, Pin.IN, pull=None)
        self.sck = Pin(sck, Pin.OUT)
        self.timeout_ms = timeout_ms

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
        start = time.ticks_ms()
        while not self.is_ready():
            if time.ticks_diff(time.ticks_ms(), start) > self.timeout_ms:
                raise OSError("HX711 timeout")
            time.sleep_ms(1)

        data = 0
        for _ in range(24):
            self.sck.value(1)
            data = (data << 1) | self.dout.value()
            self.sck.value(0)

        for _ in range(self.GAIN):
            self.sck.value(1)
            self.sck.value(0)

        if data & 0x800000:
            data |= ~0xFFFFFF

        return data

    def read(self, samples=5):
        values = []
        for _ in range(samples):
            try:
                values.append(self.read_raw())
            except OSError:
                pass

        if not values:
            raise OSError("HX711 no valid samples")

        return sum(values) / len(values)

    def tare(self, samples=10):
        self.offset = self.read(samples)

    def set_scale(self, scale):
        self.scale = scale

    def get_weight(self, samples=5):
        value = self.read(samples)
        return (value - self.offset) / self.scale
