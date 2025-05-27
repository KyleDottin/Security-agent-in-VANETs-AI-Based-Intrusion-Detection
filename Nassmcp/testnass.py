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


running = False
simulation_thread = None

traci_connection = None
step_counter = 0


#Functions
def add_vehicle_to_xml(vehicle_id, route_id, type_id, xml_path):
    # Si le fichier n'existe pas, on le crée avec une racine
    if not os.path.exists(xml_path):
        root = ET.Element("additional")
        tree = ET.ElementTree(root)
    else:
        tree = ET.parse(xml_path)
        root = tree.getroot()

    # Crée un nouvel élément vehicle
    vehicle = ET.Element("vehicle", id=vehicle_id, type=type_id, route=route_id, depart="0")
    root.append(vehicle)

    # Sauvegarde
    tree.write(xml_path)

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


@app.get("/")
def read_root():
    return {"message": "Welcome to the Simulation API"}

@app.post("/create_vehicle")
def create_vehicle():
    try:
        vehicle_id = "veh1"
        route_id = "route0"
        type_id = "car"
        xml_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\dynamic_vehicles.add.xml"

        # 1. Ajout au XML
        add_vehicle_to_xml(vehicle_id, route_id, type_id, xml_path)

        # 2. Ajout à la simulation en direct via TraCI
        traci.vehicle.add(vehID=vehicle_id, routeID=route_id, typeID=type_id)
        traci.vehicle.setColor(vehicle_id, (255, 0, 0))
        traci.vehicle.setSpeed(vehicle_id, 10.0)

        return {"status": f"Vehicle {vehicle_id} added and saved"}
    except Exception as e:
        return {"error": str(e)}

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

# @app.post("/step")
# def step():
#     global traci_connection, step_counter

#     if traci_connection is None:
#         return {"error": "Not connected to TraCI"}

#     try:
#         traci.simulationStep()
#         step_counter += 1

#         vehicles_data = []
#         vehicle_ids = traci.vehicle.getIDList()

#         for veh_id in vehicle_ids:
#             speed = traci.vehicle.getSpeed(veh_id)
#             pos = traci.vehicle.getPosition(veh_id)
#             angle = traci.vehicle.getAngle(veh_id)
#             road_id = traci.vehicle.getRoadID(veh_id)
#             veh_type = traci.vehicle.getTypeID(veh_id)
#             accel = traci.vehicle.getAcceleration(veh_id)
#             length = traci.vehicle.getLength(veh_id)
#             color = traci.vehicle.getColor(veh_id)
#             next_tls = traci.vehicle.getNextTLS(veh_id)

#             tls_info = None
#             if next_tls:
#                 tls_id, dist, state, _ = next_tls[0]
#                 tls_info = {
#                     "tls_id": tls_id,
#                     "distance": dist,
#                     "state": state
#                 }

#             vehicles_data.append({
#                 "id": veh_id,
#                 "position": pos,
#                 "speed": speed,
#                 "acceleration": accel,
#                 "angle": angle,
#                 "road_id": road_id,
#                 "vehicle_type": veh_type,
#                 "length": length,
#                 "color": color,
#                 "next_traffic_light": tls_info
#             })

#         return {
#             "step": step_counter,
#             "simulation_time": traci.simulation.getTime(),
#             "vehicles": vehicles_data
#         }

#     except Exception as e:
#         return {"error": str(e)}



