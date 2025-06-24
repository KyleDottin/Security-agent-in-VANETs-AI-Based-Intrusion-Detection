import traci
import sys
import time
import threading
import xml.etree.ElementTree as ET
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

sys.path.append(r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\veins_python")

# Global variables
running = False
simulation_thread = None
traci_connection = None
step_counter = 0
sumo_process = None
simulation_data = []

# Pydantic model for /add_vehicle
class Vehicle(BaseModel):
    vehicle_id: str
    depart: float
    from_edge: str
    to_edge: str

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
    global running, step_counter, simulation_data
    while running and traci_connection is not None:
        try:
            traci.simulationStep()
            print(f"\n--- Simulation Step: {step_counter} ---")
            step_data = collect_vehicle_data(step_counter)
            simulation_data.append(step_data)
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
        step_counter = 0
        simulation_data = []
        with open(route_file_path, "w", encoding="utf-8") as f:
            f.write(basic_content)
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

@app.get("/simulation_data")
def get_simulation_data():
    return {
        "total_steps": len(simulation_data),
        "data": simulation_data
    }

@app.get("/simulation_stats")
def get_simulation_stats():
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
