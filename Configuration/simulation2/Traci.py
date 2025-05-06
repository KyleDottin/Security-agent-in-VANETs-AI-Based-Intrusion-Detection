# Step 1: Add modules to provide access to specific libraries and functions
import os  # Module provides functions to handle file paths, directories, environment variables
import sys  # Module provides access to Python-specific system parameters and functions
import keyboard  # For keyboard input detection

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
    '--lateral-resolution', '0.1'
]

# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
vehicle_speed = 0
total_speed = 0
vehicle_stopped = False
stop_duration = 3.0  # 3 seconds in simulation time
stop_start_time = 0  # When the vehicle started stopping


# Step 7: Define Functions
def stop_vehicle(vehicle_id):
    """Stop the vehicle immediately at its current position"""
    lane_id = traci.vehicle.getLaneID(vehicle_id)
    position = traci.vehicle.getLanePosition(vehicle_id)
    edge_id = lane_id.split('_')[0]  # Extract edge ID from lane ID
    lane_index = int(lane_id.split('_')[-1])  # Extract lane index

    traci.vehicle.setStop(
        vehID=vehicle_id,
        edgeID=edge_id,
        pos=position,
        laneIndex=lane_index,
        duration=3000,  # 3 seconds in milliseconds
        flags=0
    )
    return traci.simulation.getTime()  # Return the current simulation time


# Register keyboard event for 'S' key
print("Press 'S' during simulation to make vehicle v1 stop for 3 seconds.")

# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()  # Move simulation forward 1 step
    current_time = traci.simulation.getTime()

    # Check if 'S' key was pressed
    if keyboard.is_pressed('s') and 'v1' in traci.vehicle.getIDList() and not vehicle_stopped:
        stop_start_time = stop_vehicle('v1')
        vehicle_stopped = True
        print(f"Vehicle v1 stopping at time {current_time:.2f}")

    # Check if it's time to resume after stop duration
    if vehicle_stopped and (current_time - stop_start_time) >= stop_duration:
        vehicle_stopped = False  # Reset for potential future stops
        print(f"Vehicle v1 resumed driving at time {current_time:.2f}")

    # Here you can decide what to do with simulation data at each step
    if 'v1' in traci.vehicle.getIDList():
        vehicle_speed = traci.vehicle.getSpeed('v1')
        total_speed = total_speed + vehicle_speed

    print(f"Time: {current_time:.2f} s, Vehicle speed: {vehicle_speed:.2f} m/s")

# Step 9: Close connection between SUMO and Traci
traci.close()