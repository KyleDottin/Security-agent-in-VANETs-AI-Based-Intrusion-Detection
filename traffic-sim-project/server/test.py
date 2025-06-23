import asyncio
import os
import threading
import time
import xml.etree.ElementTree as ET
from typing import Optional
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
    "simulation_thread": None
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
app = FastAPI(title="SUMO Simulation API with MCP Agent")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation de l'agent MCP
fast = FastAgent("SUMO Simulation Agent", parse_cli_args=False)

@fast.agent(instruction="""You are a SUMO traffic simulation assistant. You can help with:
- Starting and stopping SUMO simulations
- Managing vehicles in the simulation
- Monitoring traffic data
- Analyzing simulation results
- Troubleshooting simulation issues
Be helpful and provide clear explanations about traffic simulation concepts.""")
async def setup_agent():
    pass

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

# Fonctions utilitaires pour SUMO
def add_vehicle_to_route_file(vehicle_id: str, depart_time: float, from_edge: str, to_edge: str, route_file_path: str):
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
        return True
    except Exception as e:
        print(f"Error adding vehicle to route file: {e}")
        return False

def get_simulation_status():
    """Retourne le statut actuel de la simulation"""
    return {
        "running": simulation_state["running"],
        "step_counter": simulation_state["step_counter"],
        "has_connection": simulation_state["traci_connection"] is not None,
        "has_process": simulation_state["sumo_process"] is not None
    }

# Endpoints adaptés avec MCP

@app.post("/ask")
async def ask_agent(request: Request):
    """Endpoint principal pour interagir avec l'agent MCP"""
    try:
        data = await request.json()
        question = data.get("question", "")

        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # Ajouter le contexte de la simulation si disponible
        context = f"Current simulation status: {get_simulation_status()}"
        enhanced_question = f"Context: {context}\n\nQuestion: {question}"

        response = await agent_app.send(enhanced_question)
        return {"response": response, "simulation_status": get_simulation_status()}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/status")
async def get_status(request: Request):
    """Obtient le statut de la simulation via l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        status = get_simulation_status()
        question = f"Please analyze this simulation status and provide insights: {status}"
        
        response = await agent_app.send(question)
        return {
            "status": status,
            "analysis": response
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/start")
async def start_simulation_via_agent(request: Request):
    """Démarre la simulation en utilisant l'agent pour la guidance"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        if simulation_state["running"]:
            message = "Simulation is already running. What would you like to do?"
            response = await agent_app.send(message)
            return {"status": "already_running", "guidance": response}

        # Ici, vous devriez implémenter la logique de démarrage réelle
        # Pour l'instant, je simule le démarrage
        simulation_state["running"] = True
        simulation_state["step_counter"] = 0

        success_message = "Simulation started successfully. The traffic simulation is now running."
        guidance = await agent_app.send(f"The simulation has been started. Provide tips for monitoring: {success_message}")
        
        return {
            "status": "started",
            "message": success_message,
            "guidance": guidance,
            "simulation_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/simulation/stop")
async def stop_simulation_via_agent(request: Request):
    """Arrête la simulation avec guidance de l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        if not simulation_state["running"]:
            message = "Simulation is not currently running."
            response = await agent_app.send(f"User tried to stop simulation but it's not running. Provide helpful guidance: {message}")
            return {"status": "not_running", "guidance": response}

        # Arrêter la simulation
        simulation_state["running"] = False
        
        stop_message = f"Simulation stopped after {simulation_state['step_counter']} steps."
        guidance = await agent_app.send(f"Simulation stopped successfully. Provide analysis and next steps: {stop_message}")
        
        return {
            "status": "stopped",
            "message": stop_message,
            "guidance": guidance,
            "final_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/vehicle/add")
async def add_vehicle_via_agent(vehicle: Vehicle):
    """Ajoute un véhicule avec validation et guidance de l'agent"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # Valider les données du véhicule via l'agent
        validation_question = f"""
        Please validate this vehicle configuration:
        - ID: {vehicle.vehicle_id}
        - Departure time: {vehicle.depart}
        - From edge: {vehicle.from_edge}
        - To edge: {vehicle.to_edge}
        
        Is this configuration valid for a traffic simulation?
        """
        
        validation_response = await agent_app.send(validation_question)

        # Tenter d'ajouter le véhicule
        success = add_vehicle_to_route_file(
            vehicle.vehicle_id,
            vehicle.depart,
            vehicle.from_edge,
            vehicle.to_edge,
            SUMO_CONFIG["route_file_path"]
        )

        if success:
            success_message = f"Vehicle {vehicle.vehicle_id} added successfully to the simulation."
            guidance = await agent_app.send(f"Vehicle added successfully. Provide tips for vehicle management: {success_message}")
            
            return {
                "status": "success",
                "message": success_message,
                "validation": validation_response,
                "guidance": guidance,
                "vehicle": vehicle.dict()
            }
        else:
            error_message = f"Failed to add vehicle {vehicle.vehicle_id} to route file."
            troubleshooting = await agent_app.send(f"Vehicle addition failed. Provide troubleshooting steps: {error_message}")
            
            return JSONResponse({
                "status": "error",
                "message": error_message,
                "troubleshooting": troubleshooting
            }, status_code=500)

    except Exception as e:
        error_response = await agent_app.send(f"An error occurred while adding vehicle: {str(e)}. Provide troubleshooting advice.")
        return JSONResponse({
            "error": str(e),
            "troubleshooting": error_response
        }, status_code=500)

@app.post("/simulation/clear")
async def clear_simulation_via_agent(request: Request):
    """Nettoie et réinitialise la simulation avec guidance"""
    try:
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # Demander confirmation et guidance à l'agent
        confirm_question = "User wants to clear and reset the simulation. Explain what this will do and ask for confirmation."
        confirmation_guidance = await agent_app.send(confirm_question)

        # Réinitialiser l'état
        simulation_state["running"] = False
        simulation_state["step_counter"] = 0
        simulation_state["traci_connection"] = None
        simulation_state["sumo_process"] = None

        # Réinitialiser le fichier de routes
        try:
            with open(SUMO_CONFIG["route_file_path"], "w", encoding="utf-8") as f:
                f.write(BASIC_ROUTE_CONTENT)
        except Exception as e:
            print(f"Warning: Could not reset route file: {e}")

        success_message = "Simulation cleared and reset to initial state."
        next_steps = await agent_app.send(f"Simulation cleared successfully. What should the user do next? {success_message}")

        return {
            "status": "cleared",
            "message": success_message,
            "confirmation_info": confirmation_guidance,
            "next_steps": next_steps,
            "simulation_status": get_simulation_status()
        }

    except Exception as e:
        error_guidance = await agent_app.send(f"Error during simulation clear: {str(e)}. Provide recovery steps.")
        return JSONResponse({
            "error": str(e),
            "recovery_guidance": error_guidance
        }, status_code=500)

@app.post("/security/report_attack")
async def report_attack_via_agent(request: Request):
    """Signale une attaque avec analyse de l'agent"""
    try:
        data = await request.json()
        attack_details = data.get("details", "No details provided")
        
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # Analyser l'attaque via l'agent
        analysis_question = f"""
        A security attack has been reported with the following details: {attack_details}
        
        Please analyze this attack report and provide:
        1. Severity assessment
        2. Recommended immediate actions
        3. Prevention measures for the future
        """
        
        analysis = await agent_app.send(analysis_question)
        
        return {
            "status": "attack_reported",
            "timestamp": time.time(),
            "details": attack_details,
            "analysis": analysis,
            "simulation_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/security/simulate_attack")
async def simulate_attack_via_agent(request: Request):
    """Simule une attaque avec guidance de sécurité"""
    try:
        data = await request.json()
        attack_type = data.get("type", "generic")
        
        if not agent_app:
            return JSONResponse({"error": "Agent not initialized"}, status_code=503)

        # Demander guidance sur la simulation d'attaque
        security_question = f"""
        User wants to simulate a {attack_type} attack for testing purposes.
        Provide guidance on:
        1. Safety precautions
        2. What to monitor during the simulation
        3. How to analyze results
        4. Security best practices
        """
        
        security_guidance = await agent_app.send(security_question)
        
        return {
            "status": "attack_simulation_prepared",
            "attack_type": attack_type,
            "security_guidance": security_guidance,
            "timestamp": time.time(),
            "simulation_status": get_simulation_status()
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/help")
async def get_help():
    """Fournit l'aide sur l'utilisation de l'API"""
    if not agent_app:
        return JSONResponse({"error": "Agent not initialized"}, status_code=503)
    
    help_request = """
    Provide a comprehensive help guide for users of this SUMO traffic simulation API.
    Include information about:
    1. Available endpoints
    2. How to start and manage simulations
    3. Vehicle management
    4. Security features
    5. Common troubleshooting steps
    """
    
    help_response = await agent_app.send(help_request)
    
    return {
        "help": help_response,
        "endpoints": [
            "/ask - Ask questions to the simulation agent",
            "/simulation/status - Get simulation status",
            "/simulation/start - Start simulation",
            "/simulation/stop - Stop simulation",
            "/simulation/clear - Clear and reset simulation",
            "/vehicle/add - Add vehicle to simulation",
            "/security/report_attack - Report security attack",
            "/security/simulate_attack - Simulate attack for testing",
            "/help - Get this help information"
        ]
    }
