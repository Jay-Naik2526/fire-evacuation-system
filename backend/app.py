from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from graph import (find_safest_path, get_all_statuses,
                   update_zone, clear_zone)
from simulator import start_simulation, get_zone_data, trigger_fire, clear_fire
from mqtt_client import start_mqtt
from thingspeak import start_thingspeak

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def home():
    return jsonify({"message": "Fire Evacuation Backend Running!"})

@app.route("/zones")
def zones():
    return jsonify(get_zone_data())

@app.route("/path/<zone_id>")
def path(zone_id):
    p, cost = find_safest_path(zone_id)
    return jsonify({"from": zone_id, "path": p, "cost": cost})

@app.route("/status")
def status():
    return jsonify(get_all_statuses())

# ─── Socket Events ─────────────────────────────────────

@socketio.on("connect")
def on_connect():
    print("Dashboard connected!")
    socketio.emit("zone_update", get_zone_data())

@socketio.on("request_path")
def on_request_path(data):
    zone_id = data.get("zone")
    if not zone_id:
        return
    path, cost = find_safest_path(zone_id)
    socketio.emit("path_update", {
        "from":  zone_id,
        "path":  path,
        "cost":  cost
    })

@socketio.on("trigger_fire")
def on_trigger_fire(data):
    zone_id = data.get("zone")
    if not zone_id:
        return
    trigger_fire(zone_id)
    update_zone(zone_id, "FIRE")
    socketio.emit("zone_update", get_zone_data())
    # Recalculate paths for all zones
    path, cost = find_safest_path(zone_id)
    socketio.emit("path_update", {
        "from": zone_id,
        "path": path,
        "cost": cost
    })

@socketio.on("clear_fire")
def on_clear_fire(data):
    zone_id = data.get("zone")
    if not zone_id:
        return
    # Clear from simulator and graph both
    clear_fire(zone_id)
    clear_zone(zone_id)
    # Force update to dashboard immediately
    socketio.emit("zone_update", get_zone_data())
    socketio.emit("path_update", {
        "from": zone_id,
        "path": [zone_id, "cleared"],
        "cost": 0
    })

if __name__ == "__main__":
    print("Starting Fire Evacuation Backend...")
    print("Server running at http://localhost:5000")
    start_simulation(socketio)
    start_mqtt(socketio)
    start_thingspeak(get_zone_data)
    socketio.run(app, port=5000, debug=False)