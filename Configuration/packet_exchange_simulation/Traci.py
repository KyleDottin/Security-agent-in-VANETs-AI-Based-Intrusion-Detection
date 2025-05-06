# Step 1: Add modules to provide access to specific libraries and functions
import os
import sys

# Step 2: Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add Traci module
import traci

# Step 4: Define Sumo configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'traci.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
vehicle_speed = 0
total_speed = 0


# Nouvelle fonction pour gérer les feux tricolores
def manage_traffic_lights():
    # Récupérer la liste des IDs des feux
    traffic_light_ids = traci.trafficlight.getIDList()

    for tls_id in traffic_light_ids:
        # Obtenir l'état actuel du feu
        current_phase = traci.trafficlight.getPhase(tls_id)
        current_state = traci.trafficlight.getRedYellowGreenState(tls_id)

        # Afficher les informations du feu
        print(f"Feu {tls_id}: Phase {current_phase} - État {current_state}")

        # Exemple de logique de contrôle
        if "GGrr" in current_state:
            print("Feu vert pour la voie principale")
        elif "rrGG" in current_state:
            print("Feu vert pour la voie secondaire")


# Step 7: Simulation loop
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    # Gestion des feux tricolores
    manage_traffic_lights()

    # Gestion des véhicules
    if 'v1' in traci.vehicle.getIDList():
        vehicle_speed = traci.vehicle.getSpeed('v1')
        total_speed += vehicle_speed

        # Ralentir le véhicule si feu rouge devant
        next_tls = traci.vehicle.getNextTLS('v1')
        if next_tls:
            tls_id, tls_index, distance, state = next_tls[0]
            if "r" in state:
                traci.vehicle.slowDown('v1', 5, 2)  # Ralentir à 5 m/s sur 2 secondes

    print(f"Vehicle speed: {vehicle_speed} m/s")

# Step 8: Close connection
traci.close()