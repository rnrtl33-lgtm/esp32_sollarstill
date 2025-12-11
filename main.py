import time
import urequests

print("MAIN STARTED - THINGSPEAK TEST")

API_KEY = "EU6EE36IJ7WSVYP3"
counter = 0

while True:
    counter += 1
    url = "https://api.thingspeak.com/update?api_key={}&field1={}".format(API_KEY, counter)
    
    try:
        r = urequests.get(url)
        print("Sent:", counter, " → TS:", r.text)
        r.close()
    except Exception as e:
        print("ERROR sending:", e)
    
    time.sleep(15)

