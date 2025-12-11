import time, gc
from machine import Pin

API_A = "EU6EE36IJ7WSVYP3"

def send(api, value):
    try:
        import urequests
        url = "https://api.thingspeak.com/update?api_key=%s&field1=%s" % (api, value)
        r = urequests.get(url)
        r.close()
        print("Sent:", value)
    except Exception as e:
        print("SEND ERROR:", e)

gc.collect()
print("MAIN STARTED v2 — ThingSpeak Test")

i = 0
while True:
    send(API_A, i)
    i += 1
    gc.collect()
    time.sleep(15)
