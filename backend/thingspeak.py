import requests
import threading
import time

# Replace with your actual API key
WRITE_API_KEY = "XINBLCJ90QTLUU20"
BASE_URL = "https://api.thingspeak.com/update"

def status_to_number(status):
    if status == "FIRE":
        return 3
    elif status == "SMOKE":
        return 2
    else:
        return 1

def send_to_thingspeak(smoke, light, crowd, status):
    try:
        params = {
            "api_key": WRITE_API_KEY,
            "field1":  smoke,
            "field2":  light,
            "field3":  crowd,
            "field4":  status_to_number(status)
        }
        response = requests.get(BASE_URL, params=params)
        if response.text != "0":
            print(f"ThingSpeak updated! Entry: {response.text}")
        else:
            print("ThingSpeak update failed!")
    except Exception as e:
        print(f"ThingSpeak error: {e}")

def start_thingspeak(get_zone_data_fn):
    def run():
        while True:
            try:
                # Send Zone 1 data to ThingSpeak
                zone_data = get_zone_data_fn()
                z1 = zone_data.get("Z1", {})
                send_to_thingspeak(
                    smoke=z1.get("smoke",  0),
                    light=z1.get("light",  0),
                    crowd=z1.get("crowd",  0),
                    status=z1.get("status","SAFE")
                )
            except Exception as e:
                print(f"ThingSpeak thread error: {e}")
            # ThingSpeak free plan allows 1 update per 15 seconds
            time.sleep(15)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("ThingSpeak started!")