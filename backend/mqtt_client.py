import paho.mqtt.client as mqtt
import json
from graph import update_zone

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "fire/evacuation/zones"

_socketio = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Backend connected to MQTT broker!")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"MQTT connection failed: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        zone_id = data.get("zone")
        status  = data.get("status", "SAFE")
        crowd   = data.get("crowd", 0)
        smoke   = data.get("smoke", 0)
        light   = data.get("light", 0)

        print(f"MQTT received → {zone_id}: {status} (smoke={smoke}, light={light})")

        # Update graph
        update_zone(zone_id, status, crowd)

        # Push to dashboard if socketio available
        if _socketio:
            _socketio.emit("mqtt_data", {
                "zone":   zone_id,
                "status": status,
                "smoke":  smoke,
                "light":  light,
                "crowd":  crowd
            })

    except Exception as e:
        print(f"MQTT message error: {e}")

def start_mqtt(socketio):
    global _socketio
    _socketio = socketio

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "FireEvac-Backend")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()
    print("MQTT client started!")