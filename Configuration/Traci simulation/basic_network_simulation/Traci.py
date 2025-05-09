# Step 1: Add modules to provide access to specific libraries and functions
import os # Module provides functions to handle file paths, directories, environment variables
import sys # Module provides access to Python-specific system parameters and functions
import traci # Module provides access to the TraCI (Traffic Control Interface) API for controlling SUMO simulations

# Step 2: Establish path to SUMO (SUMO_HOME)

# if 'SUMO_HOME' in os.environ:
#     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
#     sys.path.append(tools)
# else:
#     sys.exit("Please declare environment variable 'SUMO_HOME'")



# 🔧 Chemin vers SUMO (ajuste si nécessaire)
# ✅ Chemin vers le dossier d'installation de SUMO (parent de 'tools' et 'bin')
sumo_home = r"C:\Program Files (x86)\Eclipse\Sumo"

# 🔧 Ajouter le dossier 'tools' à sys.path pour utiliser sumolib et traci
tools_path = os.path.join(sumo_home, 'tools')

if os.path.isdir(tools_path):
    sys.path.append(tools_path)
    print("✅ SUMO tools path ajouté avec succès :", tools_path)
else:
    sys.exit(f"❌ Le dossier 'tools' est introuvable dans : {tools_path}")   
# Step 3: Add Traci module to provide access to specific libraries and functions
import traci # Static network information (such as reading and analyzing network files)



# Step 4: Define Sumo configuration
Sumo_config = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",  # Chemin complet vers l'exécutable
    '-c', r"C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Traci simulation\basic_network_simulation\traci.sumocfg",  # Chemin vers ton fichier .sumocfg
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]



# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
vehicle_speed = 0
total_speed = 0

# Step 7: Define Functions
traci.connect(port=8813)
# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() # Move simulation forward 1 step
    # Here you can decide what to do with simulation data at each step
    if 'v1' in traci.vehicle.getIDList():
        vehicle_speed = traci.vehicle.getSpeed('v1')
        total_speed = total_speed + vehicle_speed
    # step_count = step_count + 1
    print(f"Vehicle speed: {vehicle_speed} m/s")

# Step 9: Close connection between SUMO and Traci
traci.close()
