import os
import sys
import traci

# Define path to SUMO installation
sumo_home = r"C:\Program Files (x86)\Eclipse\Sumo"
tools_path = os.path.join(sumo_home, 'tools')

if os.path.isdir(tools_path):
    sys.path.append(tools_path)
    print("SUMO tools path successfully added:", tools_path)
else:
    sys.exit(f"Error: 'tools' folder not found in {tools_path}")

# Define SUMO configuration
Sumo_config = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    '-c', r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg",
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

# Run simulation until all vehicles are gone
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    if 'v1' in traci.vehicle.getIDList():
        vehicle_speed = traci.vehicle.getSpeed('v1')
        total_speed += vehicle_speed
    print(f"Vehicle speed: {vehicle_speed} m/s")

# Close connection with TraCI
traci.close()