# Step 1: Add modules to provide access to specific libraries and functions
import os # Module provides functions to handle file paths, directories, environment variables
import sys # Module provides access to Python-specific system parameters and functions

# Step 2: Establish path to SUMO (SUMO_HOME)

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


# Step 3: Add Traci module to provide access to specific libraries and functions
import traci # Static network information (such as reading and analyzing network files)



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
vehicle_id = 'veh1'  # ID du véhicule à contrôler
vehicle_speed = 0
total_speed = 0
step_count = 0
distance_traveled = 0
previous_position = None
target_speeds = [10, 15, 5, 20]  # Vitesses cibles en m/s
current_target_index = 0
lane_change_interval = 100  # Nombre de pas entre les changements de voie
next_lane_change = lane_change_interval

# Step 7: Define Functions
def add_vehicle_if_not_exists(veh_id, route_id="route_0", veh_type="passenger"):
    """Ajoute un véhicule s'il n'existe pas déjà dans la simulation"""
    if veh_id not in traci.vehicle.getIDList():
        try:
            # Paramètres: id, route_id, type, départ, position_départ, vitesse_départ, voie_départ
            traci.vehicle.add(veh_id, route_id, veh_type, "0", "0", "0", "0")
            traci.vehicle.setColor(veh_id, (255, 0, 0, 255))  # Rouge (R,G,B,A)
            print(f"Véhicule {veh_id} ajouté à la simulation")
            return True
        except traci.exceptions.TraCIException as e:
            print(f"Erreur lors de l'ajout du véhicule: {e}")
            return False
    return True

def adjust_vehicle_speed(veh_id, target_speed):
    """Ajuste progressivement la vitesse du véhicule vers la cible"""
    current_speed = traci.vehicle.getSpeed(veh_id)
    # Ajustement progressif (max 0.5 m/s par étape)
    speed_diff = target_speed - current_speed
    adjustment = max(min(speed_diff, 0.5), -0.5)
    new_speed = current_speed + adjustment
    traci.vehicle.setSpeed(veh_id, new_speed)
    return new_speed

def change_lane_safely(veh_id):
    """Change de voie de manière sécurisée"""
    # Obtenir le nombre de voies disponibles
    current_edge = traci.vehicle.getRoadID(veh_id)
    if current_edge.startswith(":"):  # Ignorer les intersections
        return
        
    current_lane = traci.vehicle.getLaneIndex(veh_id)
    lane_count = traci.edge.getLaneNumber(current_edge)
    
    if lane_count > 1:  # S'il y a plus d'une voie
        # Choix aléatoire d'une nouvelle voie différente de l'actuelle
        possible_lanes = list(range(lane_count))
        possible_lanes.remove(current_lane)
        new_lane = random.choice(possible_lanes)
        
        print(f"Changement de voie: {current_lane} -> {new_lane}")
        traci.vehicle.changeLane(veh_id, new_lane, 5.0)  # Durée de 5 secondes

def collect_vehicle_data(veh_id):
    """Collecte et affiche des données sur le véhicule"""
    if veh_id in traci.vehicle.getIDList():
        position = traci.vehicle.getPosition(veh_id)
        speed = traci.vehicle.getSpeed(veh_id)
        lane_id = traci.vehicle.getLaneID(veh_id)
        angle = traci.vehicle.getAngle(veh_id)
        edge_id = traci.vehicle.getRoadID(veh_id)
        
        data = {
            "id": veh_id,
            "position": position,
            "speed": speed,
            "lane_id": lane_id,
            "angle": angle,
            "edge_id": edge_id
        }
        
        print(f"Données du véhicule {veh_id}:")
        print(f"  Position: ({position[0]:.2f}, {position[1]:.2f})")
        print(f"  Vitesse: {speed:.2f} m/s")
        print(f"  Voie: {lane_id}")
        print(f"  Angle: {angle:.2f}°")
        print(f"  Segment: {edge_id}")
        
        return data
    return None

def calculate_distance(pos1, pos2):
    """Calcule la distance euclidienne entre deux positions"""
    if pos1 and pos2:
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
    return 0

# Step 8: Take simulation steps until there are no more vehicles in the network
try:
    # S'assurer que le véhicule est ajouté à la simulation
    add_vehicle_if_not_exists(vehicle_id)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        # Move simulation forward 1 step
        traci.simulationStep()
        step_count += 1
        
        # Contrôler le véhicule s'il existe dans la simulation
        if vehicle_id in traci.vehicle.getIDList():
            # Ajuster la vitesse du véhicule selon la cible actuelle
            current_target = target_speeds[current_target_index]
            vehicle_speed = adjust_vehicle_speed(vehicle_id, current_target)
            total_speed += vehicle_speed
            
            # Changer de cible de vitesse tous les 200 pas
            if step_count % 200 == 0:
                current_target_index = (current_target_index + 1) % len(target_speeds)
                print(f"Nouvelle vitesse cible: {target_speeds[current_target_index]} m/s")
            
            # Changement de voie périodique
            if step_count >= next_lane_change:
                change_lane_safely(vehicle_id)
                next_lane_change = step_count + lane_change_interval
            
            # Collecter la position actuelle
            current_position = traci.vehicle.getPosition(vehicle_id)
            
            # Calculer la distance parcourue
            if previous_position:
                distance_traveled += calculate_distance(previous_position, current_position)
            previous_position = current_position
            
            # Afficher des données toutes les 50 étapes
            if step_count % 50 == 0:
                vehicle_data = collect_vehicle_data(vehicle_id)
                print(f"Distance totale parcourue: {distance_traveled:.2f} m")
                print(f"Vitesse moyenne: {total_speed/step_count:.2f} m/s")
                
                # Récupérer les véhicules à proximité
                nearby_vehicles = traci.vehicle.getIDList()
                nearby_count = len(nearby_vehicles) - 1  # Exclure notre véhicule
                if nearby_count > 0:
                    print(f"Véhicules à proximité: {nearby_count}")
        else:
            # Tenter de réintroduire le véhicule s'il a disparu
            if add_vehicle_if_not_exists(vehicle_id):
                print(f"Véhicule {vehicle_id} réintroduit dans la simulation")
            else:
                print("Impossible de réintroduire le véhicule")
                
    print("Simulation terminée - plus de véhicules dans le réseau")
    print(f"Distance totale parcourue: {distance_traveled:.2f} m")
    if step_count > 0:
        print(f"Vitesse moyenne: {total_speed/step_count:.2f} m/s")

except Exception as e:
    print(f"Erreur pendant la simulation: {e}")

finally:
    # Step 9: Close connection between SUMO and Traci
    print("Fermeture de la connexion TraCI")
    traci.close()