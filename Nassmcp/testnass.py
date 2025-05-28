import traci
import sumolib
import sys
import time
import subprocess
sys.path.append(r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\veins_python")
from fastapi import FastAPI
import xml.etree.ElementTree as ET
import os

import threading


##global
running = False
simulation_thread = None
traci_connection = None
step_counter = 0


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



def simulation_loop():
    global running, step_counter

    while running and traci_connection is not None:
        try:
            traci.simulationStep()
            print(f"\n--- Simulation Step: {step_counter} ---")
            step_counter += 1

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

                print(f"Vehicle ID: {veh_id}")
                print(f"  Position: {pos}")
                print(f"  Speed: {speed:.2f} m/s")
                print(f"  Acceleration: {accel:.2f} m/s²")
                print(f"  Angle: {angle:.2f}°")
                print(f"  Road ID: {road_id}")
                print(f"  Vehicle Type: {veh_type}")
                print(f"  Length: {length:.2f} m")
                print(f"  Color: {color}")
                if next_tls:
                    tls_id, dist, state, _ = next_tls[0]
                    print(f"  Next traffic light ID: {tls_id}, Distance: {dist:.2f} m, Light State: {state}")
            
            time.sleep(0.05)  # ou moins si tu veux que ça aille plus vite

        except Exception as e:
            print("Erreur dans la boucle de simulation:", e)
            running = False


app = FastAPI()


@app.post("/clear_simulation")
def clear_simulation():
    global running, traci_connection, simulation_thread, step_counter

    try:
        # Stop simulation loop
        running = False
        if simulation_thread and simulation_thread.is_alive():
            simulation_thread.join(timeout=2)

        # Close TraCI connection if open
        if traci_connection is not None:
            traci_connection.close()
            traci_connection = None

        # Reset simulation step counter
        step_counter = 0

        # Rewrite the route file
        route_file_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"
        route_content = '''<?xml version='1.0' encoding='UTF-8'?> 
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <trip id="v0" depart="0.00" from="E1" to="-E0.46" />
    <trip id="v1" depart="0.00" from="E0" to="E00" />
</routes>'''

        with open(route_file_path, "w", encoding="utf-8") as f:
            f.write(route_content)

        return {"status": "Simulation cleared and route file reset"}

    except Exception as e:
        return {"error": str(e)}
    
    
##curl -X POST http://127.0.0.1:8000/add_vehicle?vehicle_id=veh2&depart=5.0&from_edge=E1&to_edge=-E0.46"
@app.post("/add_vehicle")
def add_vehicle(vehicle_id: str, depart: float, from_edge: str, to_edge: str):
    route_file_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.rou.xml"

    try:
        add_vehicle_to_route_file(vehicle_id, depart, from_edge, to_edge, route_file_path)
        return {"status": f"Vehicle {vehicle_id} added to route file."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Simulation API"}

@app.post("/create_agent")
def create_agent():
    return {"status": "agent created"}

@app.post("/report_attack")
def report_attack():
    return {"status": "attack reported"}

@app.post("/simulate_attack")
def simulate_attack():
    return {"status": "attack simulated"}



@app.post("/SUMO")
def start_sumo_and_connect():
    global traci_connection
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

    traci_connection = traci.start(cmd, port=port)
    return {"status": "SUMO started and TraCI connected"}


@app.post("/start_simulation")
def start_simulation():
    global running, simulation_thread, step_counter

    if running:
        return {"status": "Simulation already running"}

    step_counter = 0
    running = True

    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

    return {"status": "Simulation started"}


@app.post("/stop_simulation")
def stop_simulation():
    global running
    running = False
    return {"status": "Simulation stopped"}

