print("=== ESP32 MAIN.PY STARTED ===")
print("This is a test version from GitHub.")
print("If you see this message, the OTA pull worked successfully!")

import time

counter = 0
while True:
    counter += 1
    print("Running test loop...  Count =", counter)
    time.sleep(2)

