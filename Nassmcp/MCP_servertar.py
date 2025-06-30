import os
import threading
from datetime import datetime
import traci
from fastmcp import FastMCP
from pydantic import BaseModel
import xml.etree.ElementTree as ET
import random

#Variable
latest_data = None
running = False
simulation_thread = None
traci_connection = None
attack_override = False
step_counter = 0
simulation_data = []
username = os.getlogin()
path1 = r"C:\Users"
# Use Othma simulation config and route files in Nassmcp
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp\othma_simulation\osm.sumocfg"
path_conf = path1 + f"\{username}" + path2
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp\othma_simulation\osm.rou.xml"
route_file_path = path1 + f"\{username}" + path2

# Add second path for files in the map folder
map_path_conf = os.path.join(path1, username, "Security-agent-in-VANETs-AI-Based-Intrusion-Detection", "Nassmcp", "map", "map.sumocfg")
map_route_file_path = os.path.join(path1, username, "Security-agent-in-VANETs-AI-Based-Intrusion-Detection", "Nassmcp", "map", "map.osm.rou.xml")


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

# Function


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
            if traffic == 1:
                check()
            step_data = collect_vehicle_data(step_counter)
            simulation_data.append(step_data)
            latest_data = step_data

        except Exception as e:
            print("Error in simulation loop:", e)
            running = False


@mcp.tool("launch_SUMO_basic")
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

@mcp.tool("launch_real_world_SUMO")
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
        "-c", map_path_conf,
        "--step-length", "0.05",
        "--delay", "1000",
        "--lateral-resolution", "0.1"
    ]

    traci_connection = traci.start(cmd, port=port)
    return {"status": "SUMO started and TraCI connected"}



@mcp.tool("create_vehicle")
def create_vehicle(vehicle: Vehicle) -> dict:
    """
    Adds and immediately starts a new vehicle in the running SUMO simulation using TraCI.
    The vehicle is added to a random available route in the simulation (the LLM/user does not provide the route).
    Returns a status message confirming the vehicle was added to the simulation, and provides the list of all available routes and edges.
    """
    global traci_connection
    try:
        if traci_connection is None:
            return {"error": "TraCI connection is not active. Start the simulation first."}
        # Get all available route IDs and edge IDs
        route_ids = traci.route.getIDList()
        edge_ids = traci.edge.getIDList()
        print("All edges in the network:", edge_ids)
        if not route_ids:
            return {"error": "No routes available in the simulation."}
        # Pick a random route
        route_id = random.choice(route_ids)
        # Add the vehicle to the simulation on the random route
        traci.vehicle.add(vehID=vehicle.vehicle_id, routeID=route_id, typeID="bus", depart=vehicle.time_departure)
        # Set initial speed to 5 m/s so the vehicle starts moving immediately
        traci.vehicle.setSpeed(vehicle.vehicle_id, 5.0)
        return {
            "status": f"Vehicle {vehicle.vehicle_id} added to simulation on route {route_id} and started at 5 m/s.",
            "all_routes": route_ids,
            "all_edges": edge_ids
        }
    except traci.TraCIException as e:
        return {"error": f"TraCI error: {e}"}
    except Exception as e:
        return {"error": str(e)}

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
    global traci_connection, attack_override
    import time

    try:
        if traci_connection is None:
            return {"error": "TraCI connection is not active. Start the simulation first."}

        attack_override = True  # Désactiver la logique de check()

        # Forcer tous les feux au rouge
        traci.trafficlight.setRedYellowGreenState("TL1", "rrrrrrrrrrrrrrr")
        for _ in range(500):
            traci.simulationStep()
            time.sleep(0.05)

        # Forcer tous les feux au vert
        traci.trafficlight.setRedYellowGreenState("TL1", "GGGGGGGGGGGGGGG")
        for _ in range(500):
            traci.simulationStep()
            time.sleep(0.05)

        return {"status": "Attack simulated: TL1 all red, then all green."}

    except Exception as e:
        return {"error": str(e)}

    finally:
        attack_override = False


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

first_time = 0
def check():
    global first_time
    global attack_override
    if attack_override:
        return
    if first_time == 0:
        for traffic_light_id in traci.trafficlight.getIDList():
            traci.trafficlight.setPhaseDuration(traffic_light_id,0)
        first_time = 1
    for traffic_light_id in traci.trafficlight.getIDList():
        if traci.trafficlight.getPhaseDuration(traffic_light_id) == 2 and traci.trafficlight.getSpentDuration(traffic_light_id)==2:
            num_phases = len(traci.trafficlight.getCompleteRedYellowGreenDefinition(traffic_light_id)[0].phases)
            next_phase = traci.trafficlight.getPhase(traffic_light_id)+1 if traci.trafficlight.getPhase(traffic_light_id)<num_phases-1 else 0
            traci.trafficlight.setPhase(traffic_light_id,next_phase)
            vehicle_count_by_route = {}
            for vehicle_id in traci.vehicle.getIDList():
                tls_data = traci.vehicle.getNextTLS(vehicle_id)
                if len(tls_data) != 0 and tls_data[0][0] == traffic_light_id and tls_data[0][2] <= 150 and tls_data[0][3].upper() == 'G':
                    route_id = traci.vehicle.getRouteID(vehicle_id)
                    if route_id in vehicle_count_by_route:
                         vehicle_count_by_route[route_id] += 1
                    else:
                        vehicle_count_by_route[route_id] = 1
            max_vehicle_count = max(vehicle_count_by_route.values()) if vehicle_count_by_route else 0
            green_light_time = min(2 + (max_vehicle_count * 2.8), 60) if max_vehicle_count!=0 else 0
            traci.trafficlight.setPhaseDuration(traffic_light_id, green_light_time)
traffic = 0
@mcp.tool("Adaptive traffic lights")
def Adaptive_Traffic_lights(action: str)-> str:
    """
    this tool launch the adaptive traffic light algorithm.
    """
    global traffic
    traffic = 1
    return "launched"


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

@mcp.tool("simulation_stats",description="Returns quick statistics about the current simulation, including total steps, unique vehicles, average speed, max speed, data points, and total fuel consumption (liters).")
def get_simulation_stats() -> dict:
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