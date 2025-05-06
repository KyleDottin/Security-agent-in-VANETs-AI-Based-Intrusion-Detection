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
# Identifiants des véhicules
vehicle_id1 = 'v1'
vehicle_id2 = 'v2'

# État des véhicules
vehicles_state = {
    vehicle_id1: {
        "position": None,
        "speed": 0,
        "lane": None,
        "route": None,
        "messages": [],
        "last_sent_time": 0,
        "target_speed": 15,
        "stopped": False,
        "communication_range": 100  # portée de communication en mètres
    },
    vehicle_id2: {
        "position": None,
        "speed": 0,
        "lane": None,
        "route": None,
        "messages": [],
        "last_sent_time": 0,
        "target_speed": 10,
        "stopped": False,
        "communication_range": 100
    }
}

# Types de messages
MESSAGE_TYPES = {
    "INFO": 0,       # Information générale
    "WARNING": 1,    # Avertissement
    "EMERGENCY": 2,  # Urgence
    "SPEED": 3,      # Information sur la vitesse
    "ROUTE": 4,      # Information sur l'itinéraire
    "STOP": 5        # Demande d'arrêt
}

step_count = 0
message_interval = 40  # Envoyer des messages tous les 40 pas (2 secondes à 0.05s par pas)

# Step 7: Define Functions
def add_vehicle_if_not_exists(veh_id, route_id, type_id="passenger", color=(255, 0, 0, 255), depart_pos="0", depart_speed="0"):
    """Ajoute un véhicule s'il n'existe pas déjà dans la simulation"""
    if veh_id not in traci.vehicle.getIDList():
        try:
            # Paramètres: id, route_id, type, départ, position_départ, vitesse_départ, voie_départ
            traci.vehicle.add(veh_id, route_id, type_id, "0", depart_pos, depart_speed, "0")
            traci.vehicle.setColor(veh_id, color)
            print(f"Véhicule {veh_id} ajouté à la simulation sur route {route_id}")
            return True
        except traci.exceptions.TraCIException as e:
            print(f"Erreur lors de l'ajout du véhicule {veh_id}: {e}")
            return False
    return True

def update_vehicle_state(veh_id):
    """Met à jour l'état du véhicule dans le dictionnaire de suivi"""
    if veh_id in traci.vehicle.getIDList():
        vehicles_state[veh_id]["position"] = traci.vehicle.getPosition(veh_id)
        vehicles_state[veh_id]["speed"] = traci.vehicle.getSpeed(veh_id)
        vehicles_state[veh_id]["lane"] = traci.vehicle.getLaneID(veh_id)
        vehicles_state[veh_id]["route"] = traci.vehicle.getRouteID(veh_id)
        return True
    return False

def calculate_distance_between_vehicles(veh_id1, veh_id2):
    """Calcule la distance entre deux véhicules"""
    pos1 = vehicles_state[veh_id1]["position"]
    pos2 = vehicles_state[veh_id2]["position"]
    
    if pos1 and pos2:
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return math.sqrt(dx*dx + dy*dy)
    return float('inf')  # Retourne l'infini si les positions ne sont pas disponibles

def is_in_communication_range(veh_id1, veh_id2):
    """Vérifie si deux véhicules sont à portée de communication"""
    distance = calculate_distance_between_vehicles(veh_id1, veh_id2)
    range1 = vehicles_state[veh_id1]["communication_range"]
    range2 = vehicles_state[veh_id2]["communication_range"]
    
    # Un véhicule est à portée si la distance est inférieure à la portée de communication
    return distance <= max(range1, range2)

def send_message(sender_id, receiver_id, msg_type, content):
    """Envoie un message d'un véhicule à un autre"""
    # Mise à jour du temps d'envoi
    vehicles_state[sender_id]["last_sent_time"] = step_count
    
    # Créer le message
    message = {
        "type": msg_type,
        "content": content,
        "sender": sender_id,
        "time": step_count,
        "delivered": False
    }
    
    # Vérifier si les véhicules sont à portée
    if is_in_communication_range(sender_id, receiver_id):
        # Ajouter le message à la file des messages du récepteur
        vehicles_state[receiver_id]["messages"].append(message)
        message["delivered"] = True
        print(f"COMMUNICATION: {sender_id} -> {receiver_id}: {MESSAGE_TYPES[msg_type]} - {content}")
        return True
    else:
        print(f"ÉCHEC COMMUNICATION: {sender_id} -> {receiver_id}: Hors de portée ({calculate_distance_between_vehicles(sender_id, receiver_id):.2f}m)")
        return False

def process_messages(veh_id):
    """Traite les messages reçus par un véhicule"""
    if not vehicles_state[veh_id]["messages"]:
        return
    
    # Traiter chaque message non traité
    unprocessed_messages = [msg for msg in vehicles_state[veh_id]["messages"] if not msg.get("processed", False)]
    
    for message in unprocessed_messages:
        sender = message["sender"]
        msg_type = message["type"]
        content = message["content"]
        
        # Marquer le message comme traité
        message["processed"] = True
        
        # Traiter selon le type de message
        if msg_type == MESSAGE_TYPES["STOP"]:
            # Demande d'arrêt d'urgence
            print(f"{veh_id} reçoit une demande d'arrêt de {sender}")
            if not vehicles_state[veh_id]["stopped"]:
                traci.vehicle.setSpeed(veh_id, 0)
                vehicles_state[veh_id]["stopped"] = True
                # Envoyer accusé de réception
                send_message(veh_id, sender, MESSAGE_TYPES["INFO"], "Arrêt en cours")
                
        elif msg_type == MESSAGE_TYPES["SPEED"]:
            # Suggestion de vitesse
            new_speed = float(content)
            print(f"{veh_id} reçoit suggestion vitesse de {sender}: {new_speed} m/s")
            if not vehicles_state[veh_id]["stopped"]:
                vehicles_state[veh_id]["target_speed"] = new_speed
                # Adapter progressivement la vitesse
                current_speed = vehicles_state[veh_id]["speed"]
                adjustment = (new_speed - current_speed) * 0.5  # Ajustement progressif
                traci.vehicle.setSpeed(veh_id, current_speed + adjustment)
                
        elif msg_type == MESSAGE_TYPES["WARNING"]:
            # Message d'avertissement, peut réduire la vitesse
            print(f"{veh_id} reçoit un avertissement de {sender}: {content}")
            if not vehicles_state[veh_id]["stopped"]:
                # Réduire la vitesse de 30%
                current_speed = vehicles_state[veh_id]["speed"]
                traci.vehicle.setSpeed(veh_id, current_speed * 0.7)
                
        elif msg_type == MESSAGE_TYPES["EMERGENCY"]:
            # Message d'urgence, arrêt immédiat
            print(f"{veh_id} reçoit un message d'URGENCE de {sender}: {content}")
            traci.vehicle.setSpeed(veh_id, 0)
            vehicles_state[veh_id]["stopped"] = True
            
    # Supprimer les messages traités plus anciens que 100 pas
    vehicles_state[veh_id]["messages"] = [
        msg for msg in vehicles_state[veh_id]["messages"] 
        if (not msg.get("processed", False)) or (step_count - msg["time"] < 100)
    ]

def display_vehicle_info(veh_id):
    """Affiche les informations sur un véhicule"""
    if veh_id in traci.vehicle.getIDList():
        state = vehicles_state[veh_id]
        pos = state["position"]
        speed = state["speed"]
        lane = state["lane"]
        
        print(f"Véhicule {veh_id}:")
        print(f"  Position: ({pos[0]:.2f}, {pos[1]:.2f})")
        print(f"  Vitesse: {speed:.2f} m/s")
        print(f"  Voie: {lane}")
        print(f"  Messages non traités: {len([m for m in state['messages'] if not m.get('processed', False)])}")
        print(f"  État d'arrêt: {'Arrêté' if state['stopped'] else 'En mouvement'}")

# Step 8: Main simulation loop
try:
    # Ajouter les véhicules à la simulation avec des routes différentes
    add_vehicle_if_not_exists(vehicle_id1, "route_0", color=(255, 0, 0, 255))  # Rouge
    add_vehicle_if_not_exists(vehicle_id2, "route_1", color=(0, 0, 255, 255), depart_pos="50")  # Bleu
    
    # Définir les vitesses initiales
    traci.vehicle.setSpeed(vehicle_id1, vehicles_state[vehicle_id1]["target_speed"])
    traci.vehicle.setSpeed(vehicle_id2, vehicles_state[vehicle_id2]["target_speed"])
    
    print("Démarrage de la simulation avec communication entre véhicules")
    
    while traci.simulation.getMinExpectedNumber() > 0:
        # Avancer la simulation d'un pas
        traci.simulationStep()
        step_count += 1
        
        # Mettre à jour l'état des véhicules
        for veh_id in [vehicle_id1, vehicle_id2]:
            update_vehicle_state(veh_id)
        
        # Vérifier si les véhicules sont à portée de communication
        if step_count % 20 == 0:  # Vérifier tous les 20 pas (1 seconde)
            in_range = is_in_communication_range(vehicle_id1, vehicle_id2)
            distance = calculate_distance_between_vehicles(vehicle_id1, vehicle_id2)
            if in_range:
                print(f"Les véhicules sont à portée de communication ({distance:.2f}m)")
            
        # Communication périodique
        if step_count % message_interval == 0:
            # Véhicule 1 envoie sa vitesse au véhicule 2
            if vehicle_id1 in traci.vehicle.getIDList():
                send_message(
                    vehicle_id1, 
                    vehicle_id2, 
                    MESSAGE_TYPES["SPEED"], 
                    str(vehicles_state[vehicle_id1]["speed"])
                )
            
            # Véhicule 2 envoie un avertissement au véhicule 1 s'il est plus lent
            if vehicle_id2 in traci.vehicle.getIDList() and step_count > message_interval * 2:
                if vehicles_state[vehicle_id2]["speed"] < vehicles_state[vehicle_id1]["speed"] * 0.7:
                    send_message(
                        vehicle_id2, 
                        vehicle_id1, 
                        MESSAGE_TYPES["WARNING"], 
                        "Vitesse réduite en avant"
                    )
        
        # Scénarios de communication spéciaux
        
        # Scénario 1: Demande d'arrêt d'urgence à l'étape 200
        if step_count == 200:
            if vehicle_id1 in traci.vehicle.getIDList() and vehicle_id2 in traci.vehicle.getIDList():
                print("\n--- SCÉNARIO: Arrêt d'urgence demandé par véhicule 1 ---")
                send_message(
                    vehicle_id1, 
                    vehicle_id2, 
                    MESSAGE_TYPES["STOP"], 
                    "Arrêt d'urgence requis"
                )
        
        # Scénario 2: Message d'urgence à l'étape 400
        if step_count == 400:
            if vehicle_id2 in traci.vehicle.getIDList() and vehicle_id1 in traci.vehicle.getIDList():
                print("\n--- SCÉNARIO: Message d'urgence envoyé par véhicule 2 ---")
                send_message(
                    vehicle_id2, 
                    vehicle_id1, 
                    MESSAGE_TYPES["EMERGENCY"], 
                    "Accident détecté! Arrêt immédiat!"
                )
        
        # Scénario 3: Reprise après arrêt à l'étape 600
        if step_count == 600:
            print("\n--- SCÉNARIO: Reprise après arrêt ---")
            for veh_id in [vehicle_id1, vehicle_id2]:
                if veh_id in traci.vehicle.getIDList():
                    vehicles_state[veh_id]["stopped"] = False
                    traci.vehicle.setSpeed(veh_id, vehicles_state[veh_id]["target_speed"])
                    # Informer l'autre véhicule
                    other_veh = vehicle_id2 if veh_id == vehicle_id1 else vehicle_id1
                    send_message(
                        veh_id, 
                        other_veh, 
                        MESSAGE_TYPES["INFO"], 
                        "Reprise du mouvement"
                    )
        
        # Traitement des messages pour chaque véhicule
        for veh_id in [vehicle_id1, vehicle_id2]:
            if veh_id in traci.vehicle.getIDList():
                process_messages(veh_id)
        
        # Afficher les informations des véhicules périodiquement
        if step_count % 100 == 0:
            print(f"\n=== État à l'étape {step_count} ===")
            for veh_id in [vehicle_id1, vehicle_id2]:
                if veh_id in traci.vehicle.getIDList():
                    display_vehicle_info(veh_id)
            print("=====================================\n")

except Exception as e:
    print(f"Erreur pendant la simulation: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Step 9: Close connection between SUMO and Traci
    print("Fermeture de la connexion TraCI")
    traci.close()