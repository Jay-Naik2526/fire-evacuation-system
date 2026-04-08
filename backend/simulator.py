import threading
import time
import random
from graph import update_zone, predict_fire_spread

# All zones in building
ALL_ZONES = [
    "Z1","Z2","Z3","Z4",
    "Z5","Z6","Z7","Z8",
    "Z9","Z10","Z11","Z12"
]

# This holds current sensor data for all zones
zone_data = {
    zone: {
        "smoke": random.randint(200, 600),
        "light": random.randint(0, 300),
        "crowd": random.randint(2, 15),
        "status": "SAFE"
    }
    for zone in ALL_ZONES
}

# Which zones are manually set on fire (triggered by dashboard)
triggered_zones = set()

def trigger_fire(zone_id):
    triggered_zones.add(zone_id)

def clear_fire(zone_id):
    triggered_zones.discard(zone_id)

def get_zone_data():
    return zone_data

def calculate_status(smoke, light):
    if smoke > 1500 and light > 2000:
        return "FIRE"
    elif smoke > 1500:
        return "SMOKE"
    else:
        return "SAFE"

def run_simulation(socketio):
    while True:
        for zone in ALL_ZONES:
            # If manually triggered → force fire values
            if zone in triggered_zones:
                zone_data[zone]["smoke"] = random.randint(2000, 4000)
                zone_data[zone]["light"] = random.randint(2500, 4000)
            else:
                # Slowly fluctuate sensor values naturally
                zone_data[zone]["smoke"] += random.randint(-100, 100)
                zone_data[zone]["light"] += random.randint(-50, 50)

                # Keep values in realistic range
                zone_data[zone]["smoke"] = max(100, min(4095, zone_data[zone]["smoke"]))
                zone_data[zone]["light"] = max(0,   min(4095, zone_data[zone]["light"]))

            # Fluctuate crowd count
            zone_data[zone]["crowd"] += random.randint(-2, 2)
            zone_data[zone]["crowd"]  = max(0, min(50, zone_data[zone]["crowd"]))

            # Calculate status
            status = calculate_status(
                zone_data[zone]["smoke"],
                zone_data[zone]["light"]
            )
            zone_data[zone]["status"] = status

            # Update graph
            update_zone(zone, status, zone_data[zone]["crowd"])

        # Predict fire spread every 10 seconds
        newly_smoke = predict_fire_spread()
        if newly_smoke:
            print(f"Fire spreading to: {newly_smoke}")

        # Send update to dashboard via socketio
        socketio.emit("zone_update", zone_data)

        time.sleep(2)

def start_simulation(socketio):
    thread = threading.Thread(
        target=run_simulation,
        args=(socketio,),
        daemon=True
    )
    thread.start()