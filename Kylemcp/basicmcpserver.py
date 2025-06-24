import os
import threading
from datetime import datetime
import traci
from fastmcp import FastMCP
from pydantic import BaseModel
import xml.etree.ElementTree as ET

#Variable
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
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
route_file_path = path1 + f"\{username}" + path2
traci_connection = None
# Read basic route file content
with open(route_file_path, "r", encoding="utf-8") as file:
    basic_content = file.read()

# Initialization of the MCP server
mcp = FastMCP("Demo")

# Class
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

# Function
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

def reset_route_file_to_basic(route_file_path, basic_content):
    """Reset the route file to its basic version"""
    try:
        with open(route_file_path, 'w', encoding='utf-8') as file:
            file.write(basic_content)
        return True
    except Exception as e:
        raise Exception(f"Failed to reset route file: {str(e)}")

@mcp.tool("launch_SUMO")
def start_sumo_and_connect() -> dict:
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

@mcp.tool("create_vehicle")
def create_vehicle(vehicle: Vehicle) -> dict :
        add_vehicle_to_route_file(
            vehicle.vehicle_id,
            vehicle.time_departure,
            vehicle.road_depart,
            vehicle.road_arrival,
            route_file_path)
        return {"status": f"Vehicle {vehicle.vehicle_id} added to route file."}

@mcp.tool("start_simulation")
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

@mcp.tool("stop_simulation")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}


@mcp.tool("report_attack")
def report_attack(attack_report: AttackReport):
    return {"message": "Attack reported successfully", "attack_report": attack_report}

@mcp.tool("simulate_attack")
def simulate_attack(simulate_attack: SimulateAttack):
    return {"message": "Attack simulated successfully", "simulate_attack": simulate_attack}

@mcp.tool("clear_simulation")
def clear_route_file() -> dict:
    global traci_connection, running, simulation_data, simulation_thread

    try:
        # Stop simulation loop
        if running:
            running = False
            if simulation_thread and simulation_thread.is_alive():
                simulation_thread.join(timeout=5)

        # Close TraCI connection
        if traci_connection is not None:
            try:
                traci.close()
            except Exception as e:
                raise Exception(f"Failed to reset route file: {str(e)}")
        traci_connection = None


        # Reset route file
        reset_route_file_to_basic(route_file_path, basic_content)

        # Clear simulation data
        simulation_data = []
        simulation_thread = None
        step_counter = 0

        return {"status": "Simulation cleared and route file reset to basic version"}
    except Exception as e:
        return {"error": f"Failed to clear simulation: {str(e)}"}



if __name__ == "__main__":
    print("MCP running at http://127.0.0.1:8000/mcp")
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"  
    )
