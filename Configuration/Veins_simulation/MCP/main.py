import threading
import asyncio
import traci
import time
import ollama
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os
import xml.etree.ElementTree as ET
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sys
import re

# Add veins_python to path
sys.path.append(r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\veins_python")

# Global variables
latest_data = None
running = False
simulation_thread = None
traci_connection = None
step_counter = 0
simulation_data = []
username = os.getlogin()
path1 = r"C:\Users"
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
path_conf = path1 + f"\{username}" + path2
path1 = r"C:\Users"
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
route_file_path = path1 + f"\{username}" + path2

# Read basic route file content
with open(route_file_path, "r", encoding="utf-8") as file:
    basic_content = file.read()

class Settings(BaseSettings):
    server_script_path: str = r"C:\Users\tru89\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Veins_simulation\MCP\Server\main.py"

settings = Settings()



def should_analyze(query: str) -> bool:
    """Determine if the query requires simulation data analysis"""
    analysis_keywords = [
        "analyze", "analysis"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in analysis_keywords)

def prepare_analysis_prompt(query: str) -> str:
    """Prepare a custom prompt for analysis based on the user's query"""
    base_prompt = f"""
You are an expert traffic analyst reviewing SUMO simulation data. 
The user has requested: "{query}"

SIMULATION DATA SUMMARY:
{{summary}}

Please provide a comprehensive analysis addressing the user's request.
Include specific insights, observations, and recommendations based on the data.
"""
    return base_prompt

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

def simulation_loop():
    global running, step_counter, simulation_data, latest_data

    while running and traci_connection is not None:
        try:
            traci.simulationStep()
            step_counter += 1

            step_data = collect_vehicle_data(step_counter)
            simulation_data.append(step_data)
            latest_data = step_data

        except Exception as e:
            print("Error in simulation loop:", e)
            running = False

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

def reset_route_file_to_basic(route_file_path, basic_content):
    """Reset the route file to its basic version"""
    try:
        with open(route_file_path, 'w', encoding='utf-8') as file:
            file.write(basic_content)
        return True
    except Exception as e:
        raise Exception(f"Failed to reset route file: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MCPClient()
    try:
        connected = await client.connect_to_server(settings.server_script_path)
        if not connected:
            print("Warning: Failed to connect to MCP server, but continuing with simulation functionality")
        app.state.client = client if connected else None
        yield
    except Exception as e:
        print(f"Warning during lifespan: {e}")
        app.state.client = None
        yield
    finally:
        if hasattr(app.state, 'client') and app.state.client:
            await app.state.client.cleanup()

app = FastAPI(title="Enhanced SUMO Simulation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class AnalysisRequest(BaseModel):
    model_name: str = "qwen3:1.7b"
    custom_prompt: str = ""

class Vehicle(BaseModel):
    vehicle_id: str
    time_departure: float
    road_depart: str
    road_arrival: str

class AttackReport(BaseModel):
    attack_id: str
    vehicle_id: str
    agent_id: str
    details: str

class SimulateAttack(BaseModel):
    attack_id: str

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("frontend/index.html")


@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        #Check if query requires simulation analysis
        if should_analyze(request.query) and simulation_data:
            print(f"Analysis request detected: {request.query}")

            custom_prompt = prepare_analysis_prompt(request.query)

            # Perform analysis with LLM
            model_name = "qwen3:1.7b"  # Default model
            analysis_result = await asyncio.to_thread(
                analyze_simulation_data_with_llm,
                model_name,
                custom_prompt
            )

            # Format response
            if 'error' in analysis_result:
                content = analysis_result['error']
            else:
                content = analysis_result.get('llm_analysis', 'Analysis completed but no content found.')

            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Analysis of simulation data for your query: '{request.query}'\n\n{content}"
                    }
                ]
            }

        # Otherwise, process with MCP client
        client = app.state.client
        messages = await client.process_query(request.query)
        return {"messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/create_vehicle")
async def create_vehicle(vehicle: Vehicle):
    try:
        add_vehicle_to_route_file(
            vehicle.vehicle_id,
            vehicle.time_departure,
            vehicle.road_depart,
            vehicle.road_arrival,
            route_file_path
        )
        return {"status": f"Vehicle {vehicle.vehicle_id} added to route file."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/report_attack")
async def report_attack(attack_report: AttackReport):
    try:
        return {"message": "Attack reported successfully", "attack_report": attack_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate_attack")
async def simulate_attack(simulate_attack: SimulateAttack):
    try:
        return {"message": "Attack simulated successfully", "simulate_attack": simulate_attack}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/SUMO")
def start_sumo_and_connect():
    global traci_connection
    sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
    port = 53517
    cmd = [
        sumo_binary,
        "-c", path_conf,
        "--step-length", "0.05",
        "--delay", "1000",
        "--lateral-resolution", "0.1"
    ]

    traci_connection = traci.start(cmd, port=port)
    return {"status": "SUMO started and TraCI connected"}

@app.post("/start_simulation")
def start_simulation():
    global running, simulation_thread, step_counter, simulation_data

    if running:
        return {"status": "Simulation already running"}

    if traci_connection is None:
        return {"error": "Not connected to TraCI"}

    step_counter = 0
    simulation_data = []
    running = True

    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

    return {"status": "Simulation started"}

@app.post("/stop_simulation")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}

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

@app.post("/clear")
def clear_route_file():
    """Reset the route file to its basic version"""
    global traci_connection, running, simulation_data

    try:
        if running:
            running = False
            if simulation_thread and simulation_thread.is_alive():
                simulation_thread.join(timeout=2)

        if traci_connection is not None:
            try:
                traci.close()
            except Exception as traci_error:
                print(f"Warning: Error closing TraCI connection: {traci_error}")
            traci_connection = None

        reset_route_file_to_basic(route_file_path, basic_content)
        simulation_data = []

        return {"status": "Route file cleared and reset to basic version"}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
