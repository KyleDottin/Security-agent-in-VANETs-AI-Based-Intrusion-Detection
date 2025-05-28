import threading
import traci
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os
import xml.etree.ElementTree as ET
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# from veins_python import VeinsPythonBridge

load_dotenv()

#Variables
latest_data = None
running = False
simulation_thread = None
traci_connection = None
step_counter = 0
username = os.getlogin()
path1 =r"C:\Users"
path2=r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
path_conf=path1+f"\{username}"+path2
path1 = r"C:\Users"
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
route_file_path = path1 + f"\{username}" + path2
with open(route_file_path, "r", encoding="utf-8") as file:
    basic_content = file.read()

class Settings(BaseSettings):
    server_script_path: str = r"C:\Users\tru89\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Veins_simulation\MCP\Server\main.py"

settings = Settings()

def simulation_loop():
    global latest_data, running, step_counter

    while running and traci_connection is not None:
        try:
            traci.simulationStep()
            step_counter += 1

            vehicles_data = []
            vehicle_ids = traci.vehicle.getIDList()

            for veh_id in vehicle_ids:
                speed = traci.vehicle.getSpeed(veh_id)
                pos = traci.vehicle.getPosition(veh_id)
                angle = traci.vehicle.getAngle(veh_id)
                road_id = traci.vehicle.getRoadID(veh_id)
                veh_type = traci.vehicle.getTypeID(veh_id)
                accel = traci.vehicle.getAcceleration(veh_id)
                length = traci.vehicle.getLength(veh_id)
                color = traci.vehicle.getColor(veh_id)
                next_tls = traci.vehicle.getNextTLS(veh_id)

                tls_info = None
                if next_tls:
                    tls_id, dist, state, _ = next_tls[0]
                    tls_info = {"tls_id": tls_id, "distance": dist, "state": state}

                vehicles_data.append({
                    "id": veh_id,
                    "position": pos,
                    "speed": speed,
                    "acceleration": accel,
                    "angle": angle,
                    "road_id": road_id,
                    "vehicle_type": veh_type,
                    "length": length,
                    "color": color,
                    "next_traffic_light": tls_info
                })

            latest_data = {
                "step": step_counter,
                "simulation_time": traci.simulation.getTime(),
                "vehicles": vehicles_data
            }

            time.sleep(0.1)

        except Exception as e:
            latest_data = {"error": str(e)}
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


def reset_route_file_to_basic(route_file_path,basic_content):
    """Reset the route file to its basic version with only the original 2 vehicles"""

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
        connected = await client.connect_to_server(settings.server_script_path) #Connection to the server
        if not connected:
            raise HTTPException(
                status_code=500, detail="Failed to connect to MCP server"
            )
        app.state.client = client
        yield
    except Exception as e:
        print(f"Error during lifespan: {e}")
        raise HTTPException(status_code=500, detail="Error during lifespan") from e
    finally:
        await client.cleanup()

app = FastAPI(title="MCP Client API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

class Message(BaseModel):
    role: str
    content: Any

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

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

# Initialize the Veins Python Bridge
# veins_bridge = VeinsPythonBridge()


@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("index.html")


# Add an endpoint to process queries using the MCP client
@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        client = app.state.client
        messages = await client.process_query(request.query)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to create a vehicle
@app.post("/create_vehicle")
async def create_vehicle(vehicle: Vehicle):

    try:
        add_vehicle_to_route_file(vehicle.vehicle_id, vehicle.time_departure, vehicle.road_depart, vehicle.road_arrival, route_file_path)
        return {"status": f"Vehicle {Vehicle.vehicle_id} added to route file."}
    except Exception as e:
        return {"error": str(e)}

# Endpoint to report an attack
@app.post("/report_attack")
async def report_attack(attack_report: AttackReport):
    try:
        # Use the Veins Python Bridge to report an attack in the simulation
        # result = veins_bridge.report_attack(attack_report.attack_id, attack_report.vehicle_id, attack_report.agent_id, attack_report.details)
        return {"message": "Attack reported successfully", "attack_report": attack_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to simulate an attack
@app.post("/simulate_attack")
async def simulate_attack(simulate_attack: SimulateAttack):
    try:
        # Use the Veins Python Bridge to simulate an attack in the simulation
        # result = veins_bridge.simulate_attack(simulate_attack.attack_id)
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
    global running, simulation_thread, step_counter, latest_data

    if running:
        return {"status": "Simulation already running"}

    if traci_connection is None:
        return {"error": "Not connected to TraCI"}

    step_counter = 0
    latest_data = None
    running = True

    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

    return {"status": "Simulation started"}

@app.post("/stop_simulation")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}


@app.post("/clear")
def clear_route_file():
    """Reset the route file to its basic version with only v0 and v1 vehicles"""
    path1 = r"C:\Users"
    path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
    route_file_path = path1 + f"\{username}" + path2
    global traci_connection, running

    try:
        # Stop the simulation if it's running
        if running:
            running = False
            if simulation_thread and simulation_thread.is_alive():
                simulation_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish

        # Close TraCI connection and SUMO simulation
        if traci_connection is not None:
            try:
                traci.close()
            except Exception as traci_error:
                print(f"Warning: Error closing TraCI connection: {traci_error}")
            traci_connection = None

        # Reset the route file
        reset_route_file_to_basic(route_file_path, basic_content)
        return {"status": "Route file cleared and reset to basic version with vehicles v0 and v1"}

    except Exception as e:
        return {"error": str(e)}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# example of command : curl -X POST "http://localhost:8000/create_vehicle" \ -H "Content-Type: application/json" \ -d "{\"vehicle_id\":\"v2\",\"time_departure\":5.0,\"road_depart\":\"E1\",\"road_arrival\":\"-E0.46\"}"
# curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d "{\"query\": \"What vehicles are currently in the simulation?\"}"
