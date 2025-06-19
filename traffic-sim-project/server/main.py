import traci
import sumolib
import sys
import time
import threading
import xml.etree.ElementTree as ET
import os
import ollama
import json
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from mcp_connection_manager import MCPConnectionManager
from pydantic import BaseModel
from typing import Any, Optional
import json
import logging

sys.path.append(r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\veins_python")

# Global variables
running = False
simulation_thread = None
traci_connection = None
step_counter = 0
sumo_process = None

# Simulation data storage
simulation_data = []

# Pydantic model for /add_vehicle
class Vehicle(BaseModel):
    vehicle_id: str
    depart: float
    from_edge: str
    to_edge: str

# Pydantic model for analysis request
class AnalysisRequest(BaseModel):
    model_name: str = "qwen3:1.7b"  # Default model
    custom_prompt: str = ""  # Optional custom prompt

# Initialize MCPConnectionManager with a lambda to fetch simulation data
mcp_manager = MCPConnectionManager(lambda: simulation_data)

# Functions
def add_vehicle_to_route_file(vehicle_id, depart_time, from_edge, to_edge, route_file_path):
    if not os.path.exists(route_file_path):
        root = ET.Element("routes")
        tree = ET.ElementTree(root)
        tree.write(route_file_path)

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

def collect_vehicle_data(step):
    """Collect vehicle data for a given step"""
    step_data = {
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "vehicles": []
    }

    vehicle_ids = traci.vehicle.getIDList()
    for veh_id in vehicle_ids:
        try:
            vehicle_data = {
                "id": veh_id,
                "speed": traci.vehicle.getSpeed(veh_id),
                "position": traci.vehicle.getPosition(veh_id),
                "angle": traci.vehicle.getAngle(veh_id),
                "road_id": traci.vehicle.getRoadID(veh_id),
                "vehicle_type": traci.vehicle.getTypeID(veh_id),
                "acceleration": traci.vehicle.getAcceleration(veh_id),
                "length": traci.vehicle.getLength(veh_id),
                "color": traci.vehicle.getColor(veh_id),
                "lane_id": traci.vehicle.getLaneID(veh_id),
                "lane_position": traci.vehicle.getLanePosition(veh_id),
                "co2_emission": traci.vehicle.getCO2Emission(veh_id),
                "fuel_consumption": traci.vehicle.getFuelConsumption(veh_id),
                "noise_emission": traci.vehicle.getNoiseEmission(veh_id)
            }

            # Traffic light information
            next_tls = traci.vehicle.getNextTLS(veh_id)
            if next_tls:
                tls_id, dist, state, _ = next_tls[0]
                vehicle_data["traffic_light"] = {
                    "id": tls_id,
                    "distance": dist,
                    "state": state
                }

            step_data["vehicles"].append(vehicle_data)

        except Exception as e:
            print(f"Error collecting data for vehicle {veh_id}: {e}")

    return step_data

def analyze_simulation_data_with_llm(model_name="qwen3:1.7b", custom_prompt=""):
    """Analyze simulation data with a local LLM via Ollama"""

    if not simulation_data:
        return {"error": "No simulation data available"}

    try:
        # Prepare general statistics
        total_steps = len(simulation_data)
        all_vehicles = set()
        speed_data = []
        acceleration_data = []
        emission_data = []

        for step_data in simulation_data:
            for vehicle in step_data["vehicles"]:
                all_vehicles.add(vehicle["id"])
                speed_data.append(vehicle["speed"])
                acceleration_data.append(vehicle["acceleration"])
                emission_data.append(vehicle["co2_emission"])

        # Calculate statistics
        stats = {
            "simulation_summary": {
                "total_steps": total_steps,
                "total_vehicles": len(all_vehicles),
                "average_speed": sum(speed_data) / len(speed_data) if speed_data else 0,
                "max_speed": max(speed_data) if speed_data else 0,
                "min_speed": min(speed_data) if speed_data else 0,
                "average_acceleration": sum(acceleration_data) / len(acceleration_data) if acceleration_data else 0,
                "total_co2_emissions": sum(emission_data) if emission_data else 0,
                "average_co2_per_vehicle": (sum(emission_data) / len(all_vehicles)) if emission_data and all_vehicles else 0
            },
            "vehicle_trajectories": []
        }

        # Analysis per vehicle
        for vehicle_id in all_vehicles:
            vehicle_trajectory = []
            for step_data in simulation_data:
                for vehicle in step_data["vehicles"]:
                    if vehicle["id"] == vehicle_id:
                        vehicle_trajectory.append({
                            "step": step_data["step"],
                            "speed": vehicle["speed"],
                            "position": vehicle["position"],
                            "acceleration": vehicle["acceleration"]
                        })

            if vehicle_trajectory:
                stats["vehicle_trajectories"].append({
                    "vehicle_id": vehicle_id,
                    "trajectory_points": len(vehicle_trajectory),
                    "avg_speed": sum(point["speed"] for point in vehicle_trajectory) / len(vehicle_trajectory),
                    "max_speed": max(point["speed"] for point in vehicle_trajectory),
                    "trajectory": vehicle_trajectory[:10]  # Limit to first 10 points for the LLM
                })

        # Construct the prompt for the LLM
        base_prompt = f"""
You are an expert in traffic analysis and SUMO simulation.
Analyze the following simulation data and provide detailed insights:

SIMULATION DATA:
{json.dumps(stats, indent=2)}

Please analyze this data and provide:
1. A general evaluation of traffic behavior
2. Observations on speed and acceleration patterns
3. An analysis of CO2 emissions
4. Recommendations to optimize traffic
5. Detection of anomalies or suspicious behaviors
6. Evaluation of traffic fluidity

Respond in English with a structured analysis and concrete recommendations.
"""

        if custom_prompt:
            prompt = f"{base_prompt}\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}"
        else:
            prompt = base_prompt

        # Call the LLM via Ollama
        print("Sending data to LLM for analysis...")
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.7,
                'num_predict': 2000
            }
        )

        analysis_result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "model_used": model_name,
            "simulation_stats": stats["simulation_summary"],
            "llm_analysis": response['message']['content'],
            "raw_data_points": len(simulation_data),
            "vehicles_analyzed": len(all_vehicles)
        }

        # Save the analysis
        analysis_filename = f"simulation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analysis_path = os.path.join(os.path.dirname(__file__), "analysis_reports", analysis_filename)

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(analysis_path), exist_ok=True)

        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        print(f"Analysis saved to: {analysis_path}")

        return analysis_result

    except Exception as e:
        print(f"Error during analysis with LLM: {e}")
        return {"error": f"Analysis error: {str(e)}"}

def simulation_loop():
    global running, step_counter, simulation_data

    while running and traci_connection is not None:
        try:
            traci.simulationStep()
            print(f"\n--- Simulation Step: {step_counter} ---")

            # Collect data for this step
            step_data = collect_vehicle_data(step_counter)
            simulation_data.append(step_data)

            # Display information (short version)
            vehicle_ids = traci.vehicle.getIDList()
            for veh_id in vehicle_ids:
                speed = traci.vehicle.getSpeed(veh_id)
                pos = traci.vehicle.getPosition(veh_id)
                print(f"Vehicle {veh_id}: Speed={speed:.2f} m/s, Position={pos}")

            step_counter += 1
            time.sleep(0.05)

        except Exception as e:
            print("Error in simulation loop:", e)
            running = False

# FastAPI app
app = FastAPI()

# CORS middleware (allow all origins for dev, restrict for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

basic_content = '''<?xml version='1.0' encoding='UTF-8'?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <trip id="v0" depart="0.00" from="E1" to="-E0.46" />
    <trip id="v1" depart="0.00" from="E0" to="E00" />
</routes>'''

@app.post("/clear_simulation")
def clear_simulation():
    global running, traci_connection, simulation_thread, step_counter, sumo_process, simulation_data

    route_file_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
    sumocfg_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
    sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
    port = 53517

    try:
        if running:
            running = False
            if simulation_thread and simulation_thread.is_alive():
                simulation_thread.join(timeout=2)

        # Attempt to close the TraCI connection
        try:
            import traci
            traci.close()
        except Exception as e:
            print(f"Warning: Error closing TraCI: {e}")

        if traci_connection is not None:
            try:
                traci_connection.close()
            except Exception as e:
                print(f"Warning: Error closing traci_connection: {e}")
            traci_connection = None

        if sumo_process:
            try:
                sumo_process.terminate()
                sumo_process.wait(timeout=5)
            except Exception as e:
                print(f"Warning: Error terminating SUMO process: {e}")
            sumo_process = None

        time.sleep(0.5)

        # Reset data
        step_counter = 0
        simulation_data = []  # Reset collected data

        with open(route_file_path, "w", encoding="utf-8") as f:
            f.write(basic_content)

        # Restart SUMO
        cmd = [
            sumo_binary,
            "-c", sumocfg_path,
            "--step-length", "0.05",
            "--delay", "1000",
            "--lateral-resolution", "0.1"
        ]

        conn, proc = traci.start(cmd, port=port)
        traci_connection = conn
        sumo_process = proc

        running = True
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()

        return {"status": "Simulation cleared, route file reset, and SUMO restarted."}

    except Exception as e:
        return {"error": str(e)}

@app.post("/add_vehicle")
def add_vehicle(vehicle: Vehicle):
    route_file_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"

    try:
        add_vehicle_to_route_file(vehicle.vehicle_id, vehicle.depart, vehicle.from_edge, vehicle.to_edge, route_file_path)
        return {"status": f"Vehicle {vehicle.vehicle_id} added to route file."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze_simulation")
def analyze_simulation(request: AnalysisRequest = AnalysisRequest()):
    """Endpoint to analyze simulation data with an LLM"""

    if not simulation_data:
        return {"error": "No simulation data available. Run a simulation first."}

    try:
        analysis_result = analyze_simulation_data_with_llm(
            model_name=request.model_name,
            custom_prompt=request.custom_prompt
        )
        return analysis_result
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}

@app.get("/simulation_data")
def get_simulation_data():
    """Endpoint to retrieve raw simulation data"""
    return {
        "total_steps": len(simulation_data),
        "data": simulation_data
    }

@app.get("/simulation_stats")
def get_simulation_stats():
    """Endpoint to get quick statistics on the simulation"""
    if not simulation_data:
        return {"message": "No data available"}

    all_vehicles = set()
    speed_data = []

    for step_data in simulation_data:
        for vehicle in step_data["vehicles"]:
            all_vehicles.add(vehicle["id"])
            speed_data.append(vehicle["speed"])

    return {
        "total_steps": len(simulation_data),
        "unique_vehicles": len(all_vehicles),
        "average_speed": sum(speed_data) / len(speed_data) if speed_data else 0,
        "max_speed": max(speed_data) if speed_data else 0,
        "data_points": len(speed_data)
    }

@app.post("/report_attack")
def report_attack():
    return {"status": "attack reported"}

@app.post("/simulate_attack")
def simulate_attack():
    return {"status": "attack simulated"}

@app.post("/SUMO")
def start_sumo_and_connect():
    global traci_connection, sumo_process
    sumocfg_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
    sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
    port = 53517
    cmd = [
        sumo_binary,
        "-c", sumocfg_path,
        "--step-length", "0.05",
        "--delay", "1000",
        "--lateral-resolution", "0.1"
    ]

    conn, proc = traci.start(cmd, port=port)
    traci_connection = conn
    sumo_process = proc

    return {"status": "SUMO started and TraCI connected"}

@app.post("/start_simulation")
def start_simulation():
    global running, simulation_thread, step_counter, simulation_data

    if running:
        return {"status": "Simulation already running"}

    step_counter = 0
    simulation_data = []  # Reset data at start

    running = True

    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

    return {"status": "Simulation started"}

@app.post("/stop_simulation")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Any] = None
    id: Optional[int] = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour logger toutes les requêtes"""
    logger.info(f"Received request: {request.method} {request.url}")
    
    # Lire le body de la requête
    body = await request.body()
    if body:
        try:
            body_json = json.loads(body.decode())
            logger.info(f"Request body: {body_json}")
        except Exception as e:
            logger.error(f"Error parsing request body: {e}")
            logger.info(f"Raw body: {body}")
    
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/mcp")
async def mcp_endpoint(request: JSONRPCRequest):
    """Endpoint MCP principal"""
    logger.info(f"MCP request received: method={request.method}, id={request.id}")
    
    try:
        method = request.method.lower()
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    },
                    "resources": {},
                    "prompts": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "Traffic Simulation MCP Server",
                    "version": "0.1.0"
                }
            }
            
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": result
            }
            
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "get_simulation_state",
                        "description": "Get current traffic simulation state",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                ]
            }
            
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": result
            }
            
        elif method == "notifications/initialized":
            # Notification d'initialisation - pas de réponse nécessaire
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {}
            }
            
        elif method == "prompts/list":
            # Liste des prompts (vide pour l'instant)
            result = {
                "prompts": []
            }
            
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": result
            }
            
        elif method == "tools/call":
            tool_name = request.params.get("name") if request.params else None
            logger.info(f"Tool call: {tool_name}")
            
            if tool_name == "get_simulation_state":
                simulation_data = {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "vehicles": [
                        {"id": "v1", "position": {"x": 100, "y": 200}, "speed": 30},
                        {"id": "v2", "position": {"x": 150, "y": 250}, "speed": 25}
                    ],
                    "traffic_lights": [
                        {"id": "tl1", "state": "green", "position": {"x": 200, "y": 300}}
                    ]
                }
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(simulation_data, indent=2)
                        }
                    ]
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool {tool_name} not found"
                    }
                }
                logger.error(f"Tool not found: {tool_name}")
                return JSONResponse(content=response)
            
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": result
            }
            
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {
                    "code": -32601,
                    "message": f"Method {request.method} not found"
                }
            }
            logger.error(f"Method not found: {request.method}")
        
        logger.info(f"Sending response: {response}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        return JSONResponse(content=error_response)

@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que le serveur fonctionne"""
    return {"status": "ok", "message": "MCP Server is running"}
