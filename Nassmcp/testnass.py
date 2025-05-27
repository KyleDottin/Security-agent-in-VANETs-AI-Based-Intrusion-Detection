import traci
import sumolib
import sys
import time
import subprocess
sys.path.append(r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\veins_python")




from fastapi import FastAPI
import xml.etree.ElementTree as ET
import os

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


@app.post("/start_sumo")
def start_sumo():
    try:
        sumocfg_path = r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
        sumo_cmd = [
            "sumo-gui",  # ou "sumo" si tu veux sans l'interface
            "-c", sumocfg_path,
            "--remote-port", "53517"
        ]

        # Démarre SUMO en tant que sous-processus
        subprocess.Popen(sumo_cmd)
        time.sleep(2)  # attend que SUMO démarre
        traci.init(port=53517)  # essaie de se connecter sur le bon port

        return {"status": "SUMO started and connected to TraCI"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/simulate_veins")
def simulate_veins():
    try:
        # Connexion au serveur Veins (OMNeT++ simulé, vérifier port)
        vc = VeinsClient(port=12345)  # adapte le port au besoin
        vc.connect()
        time.sleep(1)  # laisse le temps à la connexion

        node_id = 1  # ID du véhicule dont on veut la position

        # Récupérer la position (x, y) du node_id dans Veins
        position = vc.get_position(node_id)

        vc.close()  # fermer la connexion proprement

        return {"status": "Veins simulation triggered", "vehicle_position": position}
    except Exception as e:
        return {"error": str(e)}