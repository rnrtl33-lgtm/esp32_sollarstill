print("MAIN STARTED v2 — ThingSpeak Test")

import time
import urequests

# ==== ThingSpeak Channels ====
TS_A = "EU6EE36IJ7WSVYP3"     # API Model A
TS_B = "E8CTAK8MCUWLVQJ2"     # API Model B
TS_C = "Y1FWSOX7Z6YZ8QMU"     # API Model C
TS_D = "HG8G8BDF40LCGV99"     # API Model D

URL = "https://api.thingspeak.com/update?api_key={}&field1={}"

# ==== Loop ====
while True:
    try:
        value = int(time.time() % 1000)   # قيمة رقمية متغيرة لاختبار الارسال
        print("Sending:", value)

        # إرسال للقنوات:
        urequests.get(URL.format(TS_A, value))
        urequests.get(URL.format(TS_B, value))
        urequests.get(URL.format(TS_C, value))
        urequests.get(URL.format(TS_D, value))

        print("Sent to ThingSpeak. Waiting 15 sec...")
    except Exception as e:
        print("Error sending:", e)

    time.sleep(15)


