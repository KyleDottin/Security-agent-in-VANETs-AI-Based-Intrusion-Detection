import os
import sys
import traci
import subprocess


#Powershell command to set the environment variable
 # & "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe" -c "C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg" --remote-port 8813
# Define path to SUMO installation
sumo_home = r"C:\Program Files (x86)\Eclipse\Sumo"
tools_path = os.path.join(sumo_home, 'tools')

if os.path.isdir(tools_path):
    sys.path.append(tools_path)
    print("SUMO tools path successfully added:", tools_path)
else:
    sys.exit(f"Error: 'tools' folder not found in {tools_path}")

#Path for the configuration of the simulation
username = os.getlogin()
path1 =r"C:\Users"
path2=r"\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg"
path_conf=path1+f"\{username}"+path2

# Define Sumo configuration
Sumo_config = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",  # Chemin complet vers l'exécutable
    '-c', path_conf,  # Chemin vers ton fichier .sumocfg
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Start SUMO and connect to TraCI
traci.start(Sumo_config)

# Variables for simulation
vehicle_speed = 0
total_speed = 0

# Connect to TraCI server on port 8813
traci.connect(port=8813)

# Simulation
step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    print(f"\n--- Simulation Step: {step} ---")
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
    step += 1
# Close connection with TraCI
traci.close()