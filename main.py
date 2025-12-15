import socket, urequests

RAW_URL = "https://raw.githubusercontent.com/rnrtl33-lgtm/esp32_sollarstill/main/main.py"

def http_get(url):
    try:
        proto, _, host, path = url.split("/", 3)
        addr = socket.getaddrinfo(host, 80)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(b"GET /" + path.encode() + b" HTTP/1.0\r\nHost: " +
               host.encode() + b"\r\n\r\n")

        data = b""
        while True:
            chunk = s.recv(256)
            if not chunk:
                break
            data += chunk
        s.close()

        body = data.split(b"\r\n\r\n", 1)[1]
        return body.decode()

    except:
        return None


def fetch_remote():
    try:
        r = urequests.get(RAW_URL)
        code = r.text
        r.close()
        return code
    except:
        return None


def check_live_update(old_code):
    new_code = fetch_remote()
    if not new_code:
        return old_code, False

    if new_code.strip() == old_code.strip():
        return old_code, False

    with open("main.py", "w") as f:
        f.write(new_code)

    return new_code, True


def run_live_ota(main_func):
    try:
        with open("main.py") as f:
            code = f.read()
    except:
        return main_func()

    while True:
        code, updated = check_live_update(code)
        if updated:
            print(">>> OTA VERSION UPDATED — Running new code <<<")
            exec(code, globals())
            return
        time.sleep(15)
