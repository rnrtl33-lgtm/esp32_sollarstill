from machine import Pin
import time

relay = Pin(17, Pin.OUT, value=1)  # HIGH = OFF (Active-LOW)

print("Pump OFF - ready for test")
time.sleep(3)

print("Pump ON")
relay.value(0)    # تشغيل
time.sleep(3)

print("Pump OFF")
relay.value(1)    # إيقاف
