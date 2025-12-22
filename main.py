from machine import Pin
import time

relay = Pin(17, Pin.OUT)

# الريلاي عندك LOW-trigger
relay.value(1)   # إيقاف مبدئي

while True:
    relay.value(0)   # تشغيل المضخة
    time.sleep(5)

    relay.value(1)   # إيقاف المضخة
    time.sleep(5)
