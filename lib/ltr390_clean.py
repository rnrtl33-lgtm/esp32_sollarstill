
from machine import Pin, SoftI2C
from ltr390_clean import LTR390
import time

# استخدم نفس Bus الذي خصصته لـ LTR390 في نموذج A
i2c = SoftI2C(scl=Pin(18), sda=Pin(19), freq=100000)

print("I2C scan:", i2c.scan())

ltr = LTR390(i2c)

print("=== ALS (Light) ===")
ltr.set_als_mode()
for _ in range(5):
    print("ALS raw:", ltr.read_als())
    time.sleep(0.5)

print("=== UV ===")
ltr.set_uvs_mode()
for _ in range(5):
    print("UV raw:", ltr.read_uv())
    time.sleep(0.5)




