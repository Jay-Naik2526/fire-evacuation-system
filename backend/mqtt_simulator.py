import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "fire/evacuation/zones"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Python-ESP32-Zone1")

def connect():
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    print("ESP32 Zone 1 Simulator connected to MQTT!")

def simulate():
    smoke = random.randint(200, 600)
    light = random.randint(0, 200)

    # Slowly fluctuate
    while True:
        smoke += random.randint(-50, 50)
        light += random.randint(-20, 20)
        smoke = max(100, min(4095, smoke))
        light = max(0,   min(4095, light))

        status = "SAFE"
        if smoke > 1500 and light > 2000:
            status = "FIRE"
        elif smoke > 1500:
            status = "SMOKE"

        payload = {
            "zone":   "Z1",
            "name":   "Main Lobby",
            "floor":  1,
            "status": status,
            "smoke":  smoke,
            "light":  light,
            "crowd":  random.randint(2, 15)
        }

        client.publish(TOPIC, json.dumps(payload))
        print(f"Published: {payload}")
        time.sleep(2)

if __name__ == "__main__":
    connect()
    simulate()