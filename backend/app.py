from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from graph import find_safest_path, get_all_statuses, update_zone
from simulator import start_simulation, get_zone_data, trigger_fire, clear_fire

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ─── Routes ───────────────────────────────────────────

@app.route("/")
def home():
    return jsonify({"message": "Fire Evacuation System Backend Running!"})

@app.route("/zones")
def get_zones():
    return jsonify(get_zone_data())

@app.route("/path/<zone_id>")
def get_path(zone_id):
    path, cost = find_safest_path(zone_id)
    return jsonify({
        "from": zone_id,
        "path": path,
        "cost": cost
    })

@app.route("/trigger/fire/<zone_id>", methods=["POST"])
def trigger_fire_route(zone_id):
    trigger_fire(zone_id)
    update_zone(zone_id, "FIRE")
    socketio.emit("zone_update", get_zone_data())
    return jsonify({"message": f"Fire triggered in {zone_id}"})

@app.route("/trigger/clear/<zone_id>", methods=["POST"])
def clear_fire_route(zone_id):
    clear_fire(zone_id)
    update_zone(zone_id, "SAFE")
    socketio.emit("zone_update", get_zone_data())
    return jsonify({"message": f"{zone_id} cleared"})

@app.route("/status")
def get_status():
    return jsonify(get_all_statuses())

# ─── Socket Events ────────────────────────────────────

@socketio.on("connect")
def on_connect():
    print("Dashboard connected!")
    socketio.emit("zone_update", get_zone_data())

@socketio.on("request_path")
def on_request_path(data):
    zone_id = data.get("zone")
    path, cost = find_safest_path(zone_id)
    socketio.emit("path_update", {
        "from": zone_id,
        "path": path,
        "cost": cost
    })

@socketio.on("trigger_fire")
def on_trigger_fire(data):
    zone_id = data.get("zone")
    trigger_fire(zone_id)
    update_zone(zone_id, "FIRE")
    socketio.emit("zone_update", get_zone_data())

@socketio.on("clear_fire")
def on_clear_fire(data):
    zone_id = data.get("zone")
    clear_fire(zone_id)
    update_zone(zone_id, "SAFE")
    socketio.emit("zone_update", get_zone_data())

# ─── Start ────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Fire Evacuation Backend...")
    print("Server running at http://localhost:5000")
    start_simulation(socketio)
    socketio.run(app, port=5000, debug=False)