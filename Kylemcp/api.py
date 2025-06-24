from fastapi import FastAPI
from mcp.server import FastMCP
from typing import Dict, Any
import os
import xml.etree.ElementTree as ET
import time

# Configuration SUMO
SUMO_CONFIG = {
    "route_file_path": "data/routes.rou.xml"
}

# État de la simulation
simulation_state = {
    "running": False,
    "step_counter": 0,
    "vehicles": []
}

# Contenu de base si le fichier XML doit être réinitialisé
BASIC_ROUTE_CONTENT = '''<?xml version='1.0' encoding='UTF-8'?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
</routes>'''

# === FONCTIONS INTERNES ===
def get_simulation_status() -> Dict[str, Any]:
    return {
        "running": simulation_state["running"],
        "step_counter": simulation_state["step_counter"],
        "vehicle_count": len(simulation_state["vehicles"]),
        "vehicles": simulation_state["vehicles"]
    }

def start_simulation_internal() -> Dict[str, Any]:
    if simulation_state["running"]:
        return {"success": False, "message": "Simulation already running"}
    simulation_state["running"] = True
    simulation_state["step_counter"] = 0
    return {"success": True, "message": "Simulation started"}

def stop_simulation_internal() -> Dict[str, Any]:
    if not simulation_state["running"]:
        return {"success": False, "message": "Simulation not running"}
    simulation_state["running"] = False
    return {"success": True, "message": f"Simulation stopped after {simulation_state['step_counter']} steps"}

def clear_simulation_internal() -> Dict[str, Any]:
    simulation_state["running"] = False
    simulation_state["step_counter"] = 0
    simulation_state["vehicles"] = []

    with open(SUMO_CONFIG["route_file_path"], "w", encoding="utf-8") as f:
        f.write(BASIC_ROUTE_CONTENT)

    return {"success": True, "message": "Simulation reset"}

def add_vehicle_to_route_file(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str, route_file_path: str) -> bool:
    try:
        if not os.path.exists(route_file_path):
            with open(route_file_path, "w", encoding="utf-8") as f:
                f.write(BASIC_ROUTE_CONTENT)

        tree = ET.parse(route_file_path)
        root = tree.getroot()

        trip = ET.Element("trip", {
            "id": vehicle_id,
            "depart": str(depart_time),
            "from": from_edge,
            "to": to_edge
        })
        root.append(trip)
        tree.write(route_file_path, encoding="utf-8", xml_declaration=True)

        simulation_state["vehicles"].append({
            "id": vehicle_id,
            "depart": depart_time,
            "from": from_edge,
            "to": to_edge,
            "added_at": time.time()
        })

        return True
    except Exception as e:
        print(f"Error adding vehicle: {e}")
        return False

# === APP FASTAPI & MCP ===
app = FastAPI()
mcp = FastMCP("simulation-tools", app=app)

# === OUTILS MCP ===
@mcp.tool()
def check_simulation_status() -> Dict[str, Any]:
    return get_simulation_status()

@mcp.tool()
def start_traffic_simulation() -> Dict[str, Any]:
    return start_simulation_internal()

@mcp.tool()
def stop_traffic_simulation() -> Dict[str, Any]:
    return stop_simulation_internal()

@mcp.tool()
def clear_traffic_simulation() -> Dict[str, Any]:
    return clear_simulation_internal()

@mcp.tool()
def add_vehicle_to_simulation(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str) -> Dict[str, Any]:
    success = add_vehicle_to_route_file(vehicle_id, depart_time, from_edge, to_edge, SUMO_CONFIG["route_file_path"])
    return {
        "success": success,
        "message": f"Vehicle {vehicle_id} {'added' if success else 'failed to add'}"
    }

# === TEST SIMPLE ===
@app.get("/")
def health_check():
    return {"message": "SUMO MCP Tool Server running"}
