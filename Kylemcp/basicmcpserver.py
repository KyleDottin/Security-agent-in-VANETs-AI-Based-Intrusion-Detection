import os
import threading
from datetime import datetime
import traci
from fastmcp import FastMCP
from pydantic import BaseModel
import time

#Variable
latest_data = None
running = False
simulation_thread = None
traci_connection = None
step_counter = 0
simulation_data = []
username = os.getlogin()
path1 = r"C:\Users"
path2 = r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\othma_simulation\osm.sumocfg"
path_conf = path1 + f"\{username}" + path2
traci_connection = None

# Initialization of the MCP server
mcp = FastMCP("Demo")

# Class
class Vehicle(BaseModel):
    vehicle_id: str
    type_id: str
    route_id: str

class AttackReport(BaseModel):
    attack_id: str
    vehicle_id: str
    agent_id: str
    details: str

class SimulateAttack(BaseModel):
    attack_id: str

# Function
def add_vehicle_to_route_file(vehicle_id, type_id, route_id):
    # Add vehicle via TraCI
    traci.vehicle.add(
        vehID=vehicle_id,
        routeID=route_id,
        typeID=type_id,
        depart="now",
        departLane="first",
        departPos="base",
        departSpeed="0"
    )

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


@mcp.tool("launch_SUMO", description="launch SUMO simulation with TraCI connection")
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

@mcp.tool("create_vehicle", description="Creates a vehicle ( car or bus ) and adds it to the route file with specified the ID of the vehicle, its type and the road ID.")
def create_vehicle(vehicle: Vehicle) -> dict :
        add_vehicle_to_route_file(
            vehicle.vehicle_id,
            vehicle.type_id,
            vehicle.route_id)
        return {"status": f"Vehicle {vehicle.vehicle_id} added to route file."}

@mcp.tool("start_simulation", description= "Starts the simulation if SUMO is already launch.")
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

@mcp.tool("stop_simulation", description="Stops the simulation loop if it is running.Returns a status message indicating the simulation was stopped.")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}


@mcp.tool("report_attack", description="Reports an attack event in the simulation.")
def report_attack(attack_report: AttackReport):
    return {"message": "Attack reported successfully", "attack_report": attack_report}

@mcp.tool("simulate_attack", description= "Simulates an attack by forcing all lights of TL1 to red for a short period, then all green. Assumes the simulation is already running and TraCI is connected.")
def simulate_attack(params: dict = None) -> dict:
    global traci_connection
    try:
        if traci_connection is None:
            return {"error": "TraCI connection is not active. Start the simulation first."}

        # Duration of the blinking effect (in seconds)
        attack_duration = 10
        # Blinking period (red ↔ yellow) in seconds
        blink_period = 0.5
        # How many blinking steps
        num_blinks = int(attack_duration / blink_period / 2)

        for i in range(num_blinks):
            # Set all lights to red
            traci.trafficlight.setRedYellowGreenState("TL1", "rrrrrrrrrrrrrrr")
            traci.simulationStep()
            time.sleep(blink_period)

            # Set all lights to yellow
            traci.trafficlight.setRedYellowGreenState("TL1", "yyyyyyyyyyyyyyy")
            traci.simulationStep()
            time.sleep(blink_period)

        # Finally, set all lights to green
        traci.trafficlight.setRedYellowGreenState("TL1", "GGGGGGGGGGGGGGG")

        return {"status": "Attack simulated: TL1 blinking red/orange, then all green."}

    except Exception as e:
        return {"error": str(e)}


@mcp.tool("simulation_stats", description="Stops the simulation, closes TraCI, resets the route file to its basic version, and clears all simulation data.")
def get_simulation_stats() -> dict:
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
