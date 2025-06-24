import asyncio
import os
import threading
import time
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp_agent.core.fastagent import FastAgent

# Configuration globale
SUMO_CONFIG = {
    "route_file_path": r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml",
    "sumocfg_path": r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg",
    "sumo_binary": r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "port": 53517
}

# Variables globales pour la simulation
simulation_state = {
    "running": False,
    "step_counter": 0,
    "traci_connection": None,
    "sumo_process": None,
    "simulation_thread": None,
    "vehicles": []
}

# Modèles Pydantic
class Vehicle(BaseModel):
    vehicle_id: str
    depart: float
    from_edge: str
    to_edge: str

class SimulationQuery(BaseModel):
    question: str
    context: Optional[str] = None

# Contenu de base pour le fichier de routes
BASIC_ROUTE_CONTENT = '''<?xml version='1.0' encoding='UTF-8'?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <trip id="v0" depart="0.00" from="E1" to="-E0.46" />
    <trip id="v1" depart="0.00" from="E0" to="E00" />
</routes>'''

# FastAPI app
app = FastAPI(title="SUMO Simulation API with Enhanced MCP Agent")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# FONCTIONS UTILITAIRES POUR L'AGENT MCP
# ============================================================================

def get_simulation_status() -> Dict[str, Any]:
    """Retourne le statut détaillé de la simulation"""
    return {
        "running": simulation_state["running"],
        "step_counter": simulation_state["step_counter"],
        "has_connection": simulation_state["traci_connection"] is not None,
        "has_process": simulation_state["sumo_process"] is not None,
        "vehicle_count": len(simulation_state["vehicles"]),
        "vehicles": simulation_state["vehicles"]
    }

def add_vehicle_to_route_file(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str, route_file_path: str) -> bool:
    """Ajoute un véhicule au fichier de routes XML"""
    try:
        if not os.path.exists(route_file_path):
            root = ET.Element("routes")
            tree = ET.ElementTree(root)
            tree.write(route_file_path, encoding="UTF-8", xml_declaration=True)

        tree = ET.parse(route_file_path)
        root = tree.getroot()

        trip_attribs = {
            "id": vehicle_id,
            "depart": str(depart_time),
            "from": from_edge,
            "to": to_edge
        }
        trip = ET.Element("trip", trip_attribs)
        root.append(trip)

        tree.write(route_file_path, encoding="UTF-8", xml_declaration=True)
        
        # Ajouter à la liste des véhicules
        simulation_state["vehicles"].append({
            "id": vehicle_id,
            "depart": depart_time,
            "from": from_edge,
            "to": to_edge,
            "added_at": time.time()
        })
        
        return True
    except Exception as e:
        print(f"Error adding vehicle to route file: {e}")
        return False

def start_simulation_internal() -> Dict[str, Any]:
    """Démarre la simulation en interne"""
    if simulation_state["running"]:
        return {"success": False, "message": "Simulation already running"}
    
    try:
        # Simuler le démarrage (ici vous ajouterez la vraie logique SUMO/TraCI)
        simulation_state["running"] = True
        simulation_state["step_counter"] = 0
        
        return {"success": True, "message": "Simulation started successfully"}
    except Exception as e:
        return {"success": False, "message": f"Failed to start simulation: {str(e)}"}

def stop_simulation_internal() -> Dict[str, Any]:
    """Arrête la simulation en interne"""
    if not simulation_state["running"]:
        return {"success": False, "message": "Simulation is not running"}
    
    try:
        simulation_state["running"] = False
        final_steps = simulation_state["step_counter"]
        
        return {"success": True, "message": f"Simulation stopped after {final_steps} steps"}
    except Exception as e:
        return {"success": False, "message": f"Failed to stop simulation: {str(e)}"}

def clear_simulation_internal() -> Dict[str, Any]:
    """Nettoie la simulation en interne"""
    try:
        simulation_state["running"] = False
        simulation_state["step_counter"] = 0
        simulation_state["vehicles"] = []
        
        # Réinitialiser le fichier de routes
        with open(SUMO_CONFIG["route_file_path"], "w", encoding="utf-8") as f:
            f.write(BASIC_ROUTE_CONTENT)
        
        return {"success": True, "message": "Simulation cleared and reset"}
    except Exception as e:
        return {"success": False, "message": f"Failed to clear simulation: {str(e)}"}

# ============================================================================
# INITIALISATION DE L'AGENT MCP AVEC OUTILS
# ============================================================================

fast = FastAgent("SUMO Simulation Agent", parse_cli_args=False)

@fast.agent(instruction="""You are a SUMO traffic simulation assistant with direct access to simulation controls.

You have access to these functions:
- get_simulation_status(): Get current simulation status
- start_simulation_internal(): Start the simulation  
- stop_simulation_internal(): Stop the simulation
- clear_simulation_internal(): Clear and reset simulation
- add_vehicle_to_route_file(): Add vehicles to simulation

Always check the simulation status first before making recommendations.
Provide clear, actionable advice based on the actual state of the simulation.
When users ask about simulation operations, use the available functions to give accurate, real-time information.""")
async def setup_agent():
    pass

# Donner accès aux fonctions à l'agent
@fast.register_tool
def check_simulation_status() -> Dict[str, Any]:
    """Check the current status of the traffic simulation"""
    return get_simulation_status()

@fast.register_tool
def start_traffic_simulation() -> Dict[str, Any]:
    """Start the traffic simulation"""
    return start_simulation_internal()

@fast.register_tool
def stop_traffic_simulation() -> Dict[str, Any]:
    """Stop the traffic simulation"""
    return stop_simulation_internal()

@fast.register_tool
def clear_traffic_simulation() -> Dict[str, Any]:
    """Clear and reset the traffic simulation"""
    return clear_simulation_internal()

@fast.register_tool
def add_vehicle_to_simulation(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str) -> Dict[str, Any]:
    """Add a vehicle to the traffic simulation"""
    success = add_vehicle_to_route_file(vehicle_id, depart_time, from_edge, to_edge, SUMO_CONFIG["route_file_path"])
    if success:
        return {
            "success": True,
            "message": f"Vehicle {vehicle_id} added successfully",
            "vehicle": {
                "id": vehicle_id,
                "depart": depart_time,
                "from": from_edge,
                "to": to_edge
            }
        }
    else:
        return {
            "success": False,
            "message": f"Failed to add vehicle {vehicle_id}"
        }

agent_app = None

@app.on_event("startup")
async def startup_event():
    global agent_app

    async def run_agent():
        global agent_app
        async with fast.run() as agent:
            agent_app = agent
            await asyncio.Event().wait()

    asyncio.create_task(run_agent())

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.post("/ask")
async def ask_agent(request: Request):
    """Endpoint principal pour interagir avec l'agent MCP enrichi"""
    try:
        data = await request.json()
        question = data.get("question", "")

        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # L'agent peut maintenant utiliser ses fonctions pour obtenir des infos réelles
        response = await agent_app.send(question)
        
        return {
            "response": response,
            "simulation_status": get_simulation_status(),
            "available_functions": [
                "check_simulation_status",
                "start_traffic_simulation", 
                "stop_traffic_simulation",
                "clear_traffic_simulation",
                "add_vehicle_to_simulation"
            ]
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/status")
async def get_status_via_agent(request: Request):
    """Obtient le statut via l'agent avec analyse"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # L'agent peut maintenant vérifier le statut réel
        question = "Please check the current simulation status and provide a detailed analysis with recommendations."
        response = await agent_app.send(question)
        
        return {
            "analysis": response,
            "raw_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/start")
async def start_simulation_via_agent(request: Request):
    """Démarre la simulation via l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        question = "Please start the traffic simulation and provide guidance on what to expect."
        response = await agent_app.send(question)
        
        return {
            "response": response,
            "status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/stop")
async def stop_simulation_via_agent(request: Request):
    """Arrête la simulation via l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        question = "Please stop the traffic simulation and provide a summary of the session."
        response = await agent_app.send(question)
        
        return {
            "response": response,
            "final_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/vehicle/add")
async def add_vehicle_via_agent(vehicle: Vehicle):
    """Ajoute un véhicule via l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        question = f"Please add a vehicle with these parameters: ID={vehicle.vehicle_id}, depart={vehicle.depart}, from={vehicle.from_edge}, to={vehicle.to_edge}. Validate the configuration first."
        response = await agent_app.send(question)
        
        return {
            "response": response,
            "vehicle": vehicle.dict(),
            "simulation_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/clear")
async def clear_simulation_via_agent(request: Request):
    """Nettoie la simulation via l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        question = "Please clear and reset the simulation. Explain what this will do and confirm the reset."
        response = await agent_app.send(question)
        
        return {
            "response": response,
            "status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/help")
async def get_help():
    """Fournit l'aide via l'agent"""
    if not agent_app:
        return JSONResponse({"error": "Agent not initialized"}, status_code=503)
    
    question = "Provide comprehensive help for using this SUMO traffic simulation API. Include all available endpoints and how to use them effectively."
    response = await agent_app.send(question)
    
    return {
        "help": response,
        "current_status": get_simulation_status(),
        "endpoints": [
            "/ask - Ask questions to the simulation agent",
            "/simulation/status - Get simulation status with analysis", 
            "/simulation/start - Start simulation with guidance",
            "/simulation/stop - Stop simulation with summary",
            "/simulation/clear - Clear and reset simulation",
            "/vehicle/add - Add vehicle with validation",
            "/help - Get comprehensive help"
        ]
    }
