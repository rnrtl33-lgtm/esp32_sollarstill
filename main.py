from machine import Pin
import time

relay = Pin(17, Pin.OUT)

relay.value(0)   # OFF مؤكد
print("OFF")
time.sleep(3)

relay.value(1)   # ON
print("ON")
time.sleep(5)

relay.value(0)   # OFF
print("OFF")
