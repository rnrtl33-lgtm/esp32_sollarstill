

from machine import Pin
import time

class WindSensor:
    def __init__(self, pin, factor=1.2):
        
        self.pin = Pin(pin, Pin.IN)
        self.factor = factor

    def measure(self, duration=2):
         
        count = 0
        t_start = time.time()

        last = self.pin.value()

        while time.time() - t_start < duration:
            current = self.pin.value()
            if current != last and current == 1:
                count += 1
            last = current

        pulses_per_sec = count / duration
        speed = pulses_per_sec * self.factor   

        return round(speed, 2)

