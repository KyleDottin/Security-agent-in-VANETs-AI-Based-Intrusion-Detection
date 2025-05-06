# Step 1: Add modules to provide access to specific libraries and functions
import os  # Module provides functions to handle file paths, directories, environment variables
import sys  # Module provides access to Python-specific system parameters and functions
import csv  # For saving data to CSV files

# Step 2: Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add Traci module to provide access to specific libraries and functions
import traci  # Static network information (such as reading and analyzing network files)

# Step 4: Define Sumo configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'traci.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1',
    # Enable device.btreceiver and device.btsender for V2V communication tracking
    '--device.btreceiver.explicit', 'v0,v1',
    '--device.btsender.explicit', 'v0,v1',
    '--device.btreceiver.range', '100',  # Communication range in meters
    '--device.btreceiver.probability', '1',  # 100% probability of reception within range
    '--device.btsender.probability', '1'  # 100% probability of sending
]

# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
vehicle_speed = 0
total_speed = 0
# Data structure to store communication logs
communication_logs = []


# Step 7: Define Functions
def log_communication(step_time, sender, receiver, distance, packet_size=1024):
    """
    Log a communication event between two vehicles

    Parameters:
    step_time: Current simulation time
    sender: ID of the sending vehicle
    receiver: ID of the receiving vehicle
    distance: Distance between the vehicles
    packet_size: Size of the simulated packet in bytes
    """
    log_entry = {
        'time': step_time,
        'sender': sender,
        'receiver': receiver,
        'distance': distance,
        'packet_size': packet_size,
        'success': distance <= 100  # Successful if within range
    }
    communication_logs.append(log_entry)
    print(f"Communication: {sender} → {receiver}, Distance: {distance:.2f}m, Success: {log_entry['success']}")
    return log_entry


def calculate_vehicle_distance(id1, id2):
    """Calculate the Euclidean distance between two vehicles"""
    if id1 in traci.vehicle.getIDList() and id2 in traci.vehicle.getIDList():
        x1, y1 = traci.vehicle.getPosition(id1)
        x2, y2 = traci.vehicle.getPosition(id2)
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return float('inf')  # Return infinity if vehicles don't exist


def save_communication_logs(filename='v2v_communication_logs.csv'):
    """Save the logged communications to a CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['time', 'sender', 'receiver', 'distance', 'packet_size', 'success']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for log in communication_logs:
            writer.writerow(log)
    print(f"Communication logs saved to {filename}")


# Step 8: Take simulation steps until there are no more vehicles in the network
step_count = 0
try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Move simulation forward 1 step
        current_time = traci.simulation.getTime()
        step_count += 1

        # Simulate packet exchange between v0 and v1 every 10 steps (adjust as needed)
        if step_count % 10 == 0 and 'v0' in traci.vehicle.getIDList() and 'v1' in traci.vehicle.getIDList():
            # Calculate distance between vehicles
            distance = calculate_vehicle_distance('v0', 'v1')

            # Log v0 to v1 communication
            log_communication(current_time, 'v0', 'v1', distance)

            # Log v1 to v0 communication (reply)
            log_communication(current_time + 0.01, 'v1', 'v0', distance)

        # Here you can decide what to do with simulation data at each step
        if 'v1' in traci.vehicle.getIDList():
            vehicle_speed = traci.vehicle.getSpeed('v1')
            total_speed = total_speed + vehicle_speed

            # Print vehicle positions for debugging
            if 'v0' in traci.vehicle.getIDList():
                v0_pos = traci.vehicle.getPosition('v0')
                v1_pos = traci.vehicle.getPosition('v1')
                distance = calculate_vehicle_distance('v0', 'v1')
                print(f"Time: {current_time:.2f}s, V0 pos: {v0_pos}, V1 pos: {v1_pos}, Distance: {distance:.2f}m")

        print(f"Time: {current_time:.2f}s, Vehicle speed: {vehicle_speed:.2f} m/s")

finally:
    # Step 9: Save communication logs and close TraCI connection
    save_communication_logs()
    traci.close()
    print("Simulation ended. Communication logs saved.")