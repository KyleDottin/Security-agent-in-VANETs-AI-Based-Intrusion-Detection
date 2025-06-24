from fastapi import FastAPI
from mcp.server import FastMCP
from typing import Dict, Any

# Simule des fonctions internes (remplace par les vraies)
def get_simulation_status() -> Dict[str, Any]:
    return {"status": "running"}

def start_simulation_internal() -> Dict[str, Any]:
    return {"started": True}

def stop_simulation_internal() -> Dict[str, Any]:
    return {"stopped": True}

def clear_simulation_internal() -> Dict[str, Any]:
    return {"cleared": True}

def add_vehicle_to_route_file(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str, route_file_path: str) -> bool:
    print(f"Vehicle added to {route_file_path}: {vehicle_id}, {depart_time}, {from_edge} -> {to_edge}")
    return True

# Configuration (chemin vers ton fichier .rou.xml)
SUMO_CONFIG = {
    "route_file_path": "data/routes.rou.xml"
}

# Crée l'app FastAPI
app = FastAPI()

# Initialise le serveur MCP intégré à FastAPI
mcp = FastMCP("simulation-tools", app=app, prefix="/mcp")

# Enregistrement des outils MCP
@mcp.tool(description="Retourne le statut actuel de la simulation")
def check_simulation_status() -> Dict[str, Any]:
    return get_simulation_status()

@mcp.tool(description="Démarre la simulation de trafic SUMO")
def start_traffic_simulation() -> Dict[str, Any]:
    print("Le chat est noir")
    return start_simulation_internal()


@mcp.tool(description="Arrête la simulation de trafic SUMO")
def stop_traffic_simulation() -> Dict[str, Any]:
    return stop_simulation_internal()

@mcp.tool(description="Nettoie la simulation")
def clear_traffic_simulation() -> Dict[str, Any]:
    return clear_simulation_internal()

@mcp.tool(description="Ajoute un véhicule à la simulation avec un ID, un temps de départ, un point de départ et un point d'arrivée")
def add_vehicle_to_simulation(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str) -> Dict[str, Any]:
    success = add_vehicle_to_route_file(vehicle_id, depart_time, from_edge, to_edge, SUMO_CONFIG["route_file_path"])
    return {
        "success": success,
        "message": f"Vehicle {vehicle_id} {'added' if success else 'failed to add'}"
    }


#
@app.get("/")
def read_root():
    return {"message": "Simulation + MCP server is running"}
