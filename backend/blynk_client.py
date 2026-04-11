import requests
import threading
import time

BLYNK_AUTH_TOKEN = "oPGiRmeXBgOfJybA02-HwO7_6lxlqK41"
BLYNK_BASE_URL   = "https://blynk.cloud/external/api"

def update_pin(pin, value):
    try:
        url = f"{BLYNK_BASE_URL}/update"
        params = { "token": BLYNK_AUTH_TOKEN, f"v{pin}": value }
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            print(f"Blynk V{pin} = {value} ✅")
        else:
            print(f"Blynk error V{pin}: {r.status_code}")
    except Exception as e:
        print(f"Blynk error: {e}")

def send_zone_data(smoke, light, status, crowd=0):
    code = 2 if status == "FIRE" else 1 if status == "SMOKE" else 0
    update_pin(0, round(smoke))
    update_pin(1, round(light))
    update_pin(2, code)
    update_pin(3, f"Zone1: {status}")
    update_pin(4, round(crowd))
    update_pin(6, round(smoke))   # history smoke
    update_pin(7, code)           # history status

def notify_event(event_code):
    try:
        url = f"{BLYNK_BASE_URL}/logEvent"
        params = { "token": BLYNK_AUTH_TOKEN, "code": event_code }
        requests.get(url, params=params, timeout=5)
        print(f"Blynk event sent: {event_code} ✅")
    except Exception as e:
        print(f"Blynk event error: {e}")

def send_evacuation_path(path_list):
    if path_list and len(path_list) > 0:
        path_str = " → ".join(path_list)
        update_pin(5, path_str)
        print(f"Blynk path sent: {path_str} ✅")
def start_blynk(get_zone_data_fn):
    def run():
        prev_status = "SAFE"
        while True:
            try:
                data   = get_zone_data_fn()
                z1     = data.get("Z1", {})
                smoke  = z1.get("smoke",  0)
                light  = z1.get("light",  0)
                status = z1.get("status", "SAFE")

                send_zone_data(
                    smoke=z1.get("smoke",  0),
                    light=z1.get("light",  0),
                    status=z1.get("status","SAFE"),
                    crowd=z1.get("crowd",  0)
                )

                # Send event only when status changes
                if status != prev_status:
                    if status == "FIRE":
                        notify_event("fire_alert")
                    elif status == "SMOKE":
                        notify_event("smoke_alert")
                    prev_status = status

            except Exception as e:
                print(f"Blynk thread error: {e}")
            time.sleep(5)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("Blynk client started!")