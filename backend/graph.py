import networkx as nx

# Build the building graph
G = nx.Graph()

# Add all zones as nodes
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
    "EXIT1": {"name": "Exit 1",          "floor": 1},
    "EXIT2": {"name": "Exit 2",          "floor": 1},
    "EXIT3": {"name": "Exit 3",          "floor": 1},
    "EXIT4": {"name": "Exit 4",          "floor": 1},
}

for zone_id, data in zones.items():
    G.add_node(zone_id, **data, status="SAFE", crowd=0)

# Add corridors (edges between zones)
corridors = [
    # Floor 1 connections
    ("Z1", "Z2"),
    ("Z2", "Z3"),
    ("Z3", "Z4"),
    ("Z1", "Z4"),
    # Floor 1 to exits
    ("Z1", "EXIT1"),
    ("Z2", "EXIT2"),
    ("Z3", "EXIT3"),
    ("Z4", "EXIT4"),
    # Floor 1 to Floor 2 (stairs)
    ("Z4", "Z5"),
    # Floor 2 connections
    ("Z5", "Z6"),
    ("Z6", "Z7"),
    ("Z7", "Z8"),
    ("Z5", "Z8"),
    # Floor 2 to Floor 3 (stairs)
    ("Z8", "Z9"),
    # Floor 3 connections
    ("Z9",  "Z10"),
    ("Z10", "Z11"),
    ("Z11", "Z12"),
    ("Z9",  "Z12"),
]

for u, v in corridors:
    G.add_edge(u, v, weight=1)

# Zone statuses stored here
zone_statuses = {z: "SAFE" for z in zones}
zone_crowd    = {z: 0     for z in zones}

def update_zone(zone_id, status, crowd=0):
    zone_statuses[zone_id] = status
    zone_crowd[zone_id]    = crowd
    if zone_id in G.nodes:
        G.nodes[zone_id]["status"] = status
        G.nodes[zone_id]["crowd"]  = crowd

def get_edge_weight(u, v):
    # Weight based on destination zone status
    status = zone_statuses.get(v, "SAFE")
    crowd  = zone_crowd.get(v, 0)
    if status == "FIRE":
        return 9999
    elif status == "SMOKE":
        return 50
    else:
        return 1 + (crowd * 0.5)

def find_safest_path(from_zone):
    exits = ["EXIT1", "EXIT2", "EXIT3", "EXIT4"]
    best_path = None
    best_cost = float("inf")

    for exit in exits:
        try:
            # Use dynamic weights
            path = nx.dijkstra_path(
                G, from_zone, exit,
                weight=lambda u, v, d: get_edge_weight(u, v)
            )
            cost = sum(
                get_edge_weight(path[i], path[i+1])
                for i in range(len(path)-1)
            )
            if cost < best_cost:
                best_cost = cost
                best_path = path
        except nx.NetworkXNoPath:
            continue

    return best_path, best_cost

def get_all_statuses():
    return zone_statuses

def predict_fire_spread():
    # If a zone is on FIRE, its SAFE neighbors become SMOKE
    newly_smoke = []
    for zone, status in zone_statuses.items():
        if status == "FIRE":
            for neighbor in G.neighbors(zone):
                if zone_statuses.get(neighbor) == "SAFE":
                    newly_smoke.append(neighbor)
    for z in newly_smoke:
        zone_statuses[z] = "SMOKE"
    return newly_smoke