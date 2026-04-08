import networkx as nx

G = nx.Graph()

zones = {
    "Z1":  {"name": "Main Lobby",       "floor": 1},
    "Z2":  {"name": "Cafeteria",         "floor": 1},
    "Z3":  {"name": "Admin Block",       "floor": 1},
    "Z4":  {"name": "Utility Room",      "floor": 1},
    "Z5":  {"name": "Lab A",             "floor": 2},
    "Z6":  {"name": "Lab B",             "floor": 2},
    "Z7":  {"name": "Staff Lounge",      "floor": 2},
    "Z8":  {"name": "HOD Office",        "floor": 2},
    "Z9":  {"name": "Server Room",       "floor": 3},
    "Z10": {"name": "Conference Hall",   "floor": 3},
    "Z11": {"name": "Director Office",   "floor": 3},
    "Z12": {"name": "Records Room",      "floor": 3},
    "EXIT1": {"name": "Exit 1", "floor": 1},
    "EXIT2": {"name": "Exit 2", "floor": 1},
    "EXIT3": {"name": "Exit 3", "floor": 1},
    "EXIT4": {"name": "Exit 4", "floor": 1},
}

for zone_id, data in zones.items():
    G.add_node(zone_id, **data, status="SAFE", crowd=0)

corridors = [
    # Floor 1 internal
    ("Z1", "Z2"), ("Z2", "Z3"), ("Z3", "Z4"), ("Z1", "Z4"),
    # Floor 1 to exits
    ("Z1", "EXIT1"), ("Z2", "EXIT2"), ("Z3", "EXIT3"), ("Z4", "EXIT4"),
    # Floor 1 to Floor 2 (multiple staircases)
    ("Z1", "Z5"), ("Z4", "Z5"), ("Z3", "Z7"),
    # Floor 2 internal
    ("Z5", "Z6"), ("Z6", "Z7"), ("Z7", "Z8"), ("Z5", "Z8"),
    # Floor 2 to Floor 3 (multiple staircases)
    ("Z8", "Z9"), ("Z7", "Z11"), ("Z6", "Z10"), ("Z5", "Z12"),
    # Floor 3 internal
    ("Z9", "Z10"), ("Z10", "Z11"), ("Z11", "Z12"), ("Z9", "Z12"),
]

for u, v in corridors:
    G.add_edge(u, v, weight=1)

zone_statuses = {z: "SAFE" for z in zones}
zone_crowd    = {z: 0      for z in zones}

def update_zone(zone_id, status, crowd=0):
    zone_statuses[zone_id] = status
    zone_crowd[zone_id]    = crowd

def clear_zone(zone_id):
    zone_statuses[zone_id] = "SAFE"
    zone_crowd[zone_id]    = 0

def get_all_statuses():
    return dict(zone_statuses)

def find_safest_path(from_zone):
    exits = ["EXIT1", "EXIT2", "EXIT3", "EXIT4"]

    # Remove ALL fire and smoke zones from graph
    blocked = set()
    for z, s in zone_statuses.items():
        if s in ("FIRE", "SMOKE"):
            blocked.add(z)

    # Always keep the starting zone
    blocked.discard(from_zone)

    # Build clean subgraph
    allowed = set(G.nodes) - blocked
    sub = G.subgraph(allowed)

    best_path = None
    best_cost = float("inf")

    # Try clean path first
    for exit in exits:
        if exit not in sub.nodes:
            continue
        if from_zone not in sub.nodes:
            continue
        try:
            path = nx.shortest_path(sub, from_zone, exit)
            if len(path) < best_cost:
                best_cost = len(path)
                best_path = path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    # If clean path found return it
    if best_path:
        return best_path, best_cost

    # No clean path — try allowing SMOKE zones as last resort
    smoke_allowed = set(G.nodes) - {
        z for z, s in zone_statuses.items() if s == "FIRE"
    }
    smoke_allowed.discard(from_zone)
    smoke_allowed.add(from_zone)
    sub2 = G.subgraph(smoke_allowed)

    for exit in exits:
        try:
            path = nx.shortest_path(sub2, from_zone, exit)
            if len(path) < best_cost:
                best_cost = len(path)
                best_path = path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    if best_path:
        return best_path, best_cost

    return ["No safe path found"], 99999

def predict_fire_spread():
    newly_smoke = []
    for zone, status in list(zone_statuses.items()):
        if status == "FIRE":
            for neighbor in G.neighbors(zone):
                if zone_statuses.get(neighbor) == "SAFE":
                    zone_statuses[neighbor] = "SMOKE"
                    newly_smoke.append(neighbor)
    return newly_smoke