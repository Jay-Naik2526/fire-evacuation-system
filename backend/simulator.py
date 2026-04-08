import threading
import time
import random
from graph import update_zone, predict_fire_spread

ALL_ZONES = [
    "Z1","Z2","Z3","Z4",
    "Z5","Z6","Z7","Z8",
    "Z9","Z10","Z11","Z12"
]

# Start all zones as SAFE with low sensor values
zone_data = {
    zone: {
        "smoke": random.randint(100, 400),
        "light": random.randint(0, 100),
        "crowd": random.randint(2, 10),
        "status": "SAFE"
    }
    for zone in ALL_ZONES
}

triggered_zones = set()

def trigger_fire(zone_id):
    triggered_zones.add(zone_id)
    zone_data[zone_id]["smoke"] = 3000
    zone_data[zone_id]["light"] = 3000
    zone_data[zone_id]["status"] = "FIRE"

def clear_fire(zone_id):
    triggered_zones.discard(zone_id)
    if zone_id in zone_data:
        zone_data[zone_id]["smoke"] = 200
        zone_data[zone_id]["light"] = 50
        zone_data[zone_id]["status"] = "SAFE"

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
            if zone in triggered_zones:
                # Keep fire values high
                zone_data[zone]["smoke"] = random.randint(2500, 4000)
                zone_data[zone]["light"] = random.randint(2500, 4000)
                zone_data[zone]["status"] = "FIRE"
            else:
                # Only fluctuate slightly — stay in SAFE range
                zone_data[zone]["smoke"] += random.randint(-20, 20)
                zone_data[zone]["light"] += random.randint(-10, 10)

                # Keep values safely below thresholds
                zone_data[zone]["smoke"] = max(100, min(800, zone_data[zone]["smoke"]))
                zone_data[zone]["light"] = max(0,   min(500, zone_data[zone]["light"]))

                zone_data[zone]["status"] = "SAFE"

            # Crowd fluctuation
            zone_data[zone]["crowd"] += random.randint(-1, 1)
            zone_data[zone]["crowd"]  = max(0, min(50, zone_data[zone]["crowd"]))

            # Update graph
            update_zone(
                zone,
                zone_data[zone]["status"],
                zone_data[zone]["crowd"]
            )

        # Fire spread every 15 seconds
        newly_smoke = predict_fire_spread()
        if newly_smoke:
            for z in newly_smoke:
                zone_data[z]["status"] = "SMOKE"
                zone_data[z]["smoke"]  = 1800
            print(f"Fire spreading to: {newly_smoke}")

        # Push update to dashboard
        socketio.emit("zone_update", zone_data)
        time.sleep(2)

def start_simulation(socketio):
    thread = threading.Thread(
        target=run_simulation,
        args=(socketio,),
        daemon=True
    )
    thread.start()