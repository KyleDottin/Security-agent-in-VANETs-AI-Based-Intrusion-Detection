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
# Use Othma simulation config and route files in Nassmcp
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp\othma_simulation\osm.sumocfg"
path_conf = path1 + f"\{username}" + path2
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp\othma_simulation\osm.rou.xml"
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
    """
    Launches the SUMO traffic simulator and establishes a TraCI connection.
    Returns a status message indicating whether the connection was successful.
    Use this tool before starting any simulation steps or vehicle operations.
    """
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
    """
    Adds a new vehicle to the simulation route file.
    Parameters:
        vehicle: Vehicle (vehicle_id, time_departure, road_depart, road_arrival)
    Returns a status message confirming the vehicle was added.
    """
    add_vehicle_to_route_file(
        vehicle.vehicle_id,
        vehicle.time_departure,
        vehicle.road_depart,
        vehicle.road_arrival,
        route_file_path)
    return {"status": f"Vehicle {vehicle.vehicle_id} added to route file."}

@mcp.tool("start_simulation")
def start_simulation():
    """
    Starts the simulation loop in a background thread.
    Returns a status message indicating if the simulation started or was already running.
    Requires SUMO/TraCI to be connected first.
    """
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
    """
    Stops the simulation loop if it is running.
    Returns a status message indicating the simulation was stopped.
    """
    global running
    running = False
    return {"status": "Simulation stopped"}


@mcp.tool("report_attack")
def report_attack(attack_report: AttackReport):
    """
    Reports an attack event in the simulation.
    Parameters:
        attack_report: AttackReport (attack_id, vehicle_id, agent_id, details)
    Returns a confirmation message and the report data.
    """
    return {"message": "Attack reported successfully", "attack_report": attack_report}

@mcp.tool("simulate_attack")
def simulate_attack(params: dict = None) -> dict:
    """
    Simulates an attack by forcing all lights of TL1 to red for a short period, then all green.
    Assumes the simulation is already running and TraCI is connected.
    """
    global traci_connection
    import time
    try:
        if traci_connection is None:
            return {"error": "TraCI connection is not active. Start the simulation first."}
        # Set all lights to red
        traci.trafficlight.setRedYellowGreenState("TL1", "rrrrrrrrrrrrrrr")
        # Wait for 2 seconds (simulation time: run a few steps)
        for _ in range(500):
            traci.simulationStep()
            time.sleep(0.05)
        # Set all lights to green
        traci.trafficlight.setRedYellowGreenState("TL1", "GGGGGGGGGGGGGGG")
        return {"status": "Attack simulated: TL1 all red, then all green."}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("clear_simulation")
def clear_route_file() -> dict:
    """
    Stops the simulation, closes TraCI, resets the route file to its basic version, and clears all simulation data.
    Returns a status message indicating the simulation was cleared and the route file reset.
    """
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

@mcp.tool("Green Light Estimation")
def green_light_time_estimator(number_of_vehicles: list)-> float:
    """
    Estimates the optimal green light duration for a traffic phase based on the number of vehicles per lane/phase.
    Parameters:
        number_of_vehicles: list of vehicle counts per phase/lane.
    Returns the estimated green light time in seconds (max 60s).
    """
    maximum = max(number_of_vehicles)
    green_light_time = 2 + (maximum * 2.8) if maximum!=0 else 0
    return min(green_light_time,60)

@mcp.tool
def test_endpoint(params: dict = None) -> dict:
    """
    A test endpoint for health checks. Prints and returns a basic message to confirm the MCP server is running.
    """
    print("Test endpoint called: Hello from MCP server!")
    return {"message": "Salut Nassim, MCP server is running!"}

energy = 0.0

def fuel_consumption():
    """
    Computes the total fuel consumption (in liters) for all moving vehicles in the current simulation step.
    Adds a small penalty (0.25) for stopped vehicles.
    Updates the global 'energy' variable.
    """
    global energy
    if traci.vehicle.getIDCount() == 0:
        return energy
    for vid in traci.vehicle.getIDList():
        if traci.vehicle.getSpeed(vid) > 0:
            energy += traci.vehicle.getFuelConsumption(vid) / 1000.0
        else:
            energy += 0.25
    return energy

@mcp.tool("simulation_stats")
def get_simulation_stats() -> dict:
    """
    Returns quick statistics about the current simulation, including total steps, unique vehicles, average speed, max speed, data points, and total fuel consumption (liters).
    """
    global energy
    if not simulation_data:
        return {"message": "No data available"}

    all_vehicles = set()
    speed_data = []

    for step_data in simulation_data:
        for vehicle in step_data["vehicles"]:
            all_vehicles.add(vehicle["id"])
            speed_data.append(vehicle["speed"])

    # Call fuel_consumption to update and get the total
    total_fuel = fuel_consumption()

    return {
        "total_steps": len(simulation_data),
        "unique_vehicles": len(all_vehicles),
        "average_speed": sum(speed_data) / len(speed_data) if speed_data else 0,
        "max_speed": max(speed_data) if speed_data else 0,
        "data_points": len(speed_data),
        "total_fuel_consumption_liters": total_fuel
    }

@mcp.tool("sumo_test", description="Launches SUMO GUI with the current simulation config in a subprocess for testing.")
def sumo_test(params: dict = None) -> dict:
    """
    Launches SUMO GUI with the current Othma simulation config (osm.sumocfg) in a subprocess.
    This tool is for testing the SUMO scenario visually, outside of TraCI control.
    Adds a delay of 1000ms to the simulation.
    """
    import subprocess
    sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
    config_file = path_conf  # Should point to the Othma simulation config
    try:
        subprocess.Popen([
            sumo_binary,
            "-c", config_file,
            "--delay", "1000"
        ], shell=False)
        return {"status": f"SUMO GUI launched with config: {config_file} and delay 1000ms"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("MCP running at http://127.0.0.1:8000/mcp")
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"  
    )



#to start
#fast-agent go --url=http://127.0.0.1:8000/mcp --auth=token

#fast-agent go --config-path fastagent.config.yaml --name summarizer --prompt-file prompt.txt --url http://127.0.0.1:8000/mcp --auth token
#fast-agent go --config-path fastagent.config.yaml --name basic_agent --url http://127.0.0.1:8000/mcp --auth token