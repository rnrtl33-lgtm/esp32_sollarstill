from machine import Pin
import time

class HX711:
    def __init__(self, dout, sck):
        self.dout = Pin(dout, Pin.IN)
        self.sck = Pin(sck, Pin.OUT)
        self.sck.off()

    def read(self):
        while self.dout.value() == 1:
            pass

        count = 0
        for _ in range(24):
            self.sck.on()
            count = count << 1
            self.sck.off()
            if self.dout.value():
                count += 1

        self.sck.on()
        self.sck.off()

        if count & 0x800000:
            count -= 0x1000000

        return count

    def read_average(self, n=10):
        total = 0
        for _ in range(n):
            total += self.read()
        return total // n

