# Step 1: Add modules to provide access to specific libraries and functions
import os  # Module provides functions to handle file paths, directories, environment variables
import sys  # Module provides access to Python-specific system parameters and functions

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
stop_start_time = None  # When the vehicle starts stopping
stop_duration = 3.0  # Duration of stop in seconds
is_stopping = False  # Flag to track if the vehicle is in stopping mode
has_stopped = False  # Flag to track if the vehicle has already been stopped

# Step 7: Define Functions

# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()  # Move simulation forward 1 step
    current_time = traci.simulation.getTime()

    # Here you can decide what to do with simulation data at each step
    if 'v1' in traci.vehicle.getIDList():
        # If the vehicle hasn't been stopped yet and is not currently stopping, initiate stop
        # We'll start the stop after the vehicle has been in the simulation for a bit
        if not has_stopped and not is_stopping and current_time > 5.0:
            # Command the vehicle to stop
            traci.vehicle.setSpeed('v1', 0.0)
            stop_start_time = current_time
            is_stopping = True
            print(f"Vehicle v1 starting to stop at time {current_time}")

        # If the vehicle is stopping and 3 seconds have passed, resume normal driving
        if is_stopping and (current_time - stop_start_time) >= stop_duration:
            # Resume normal driving by setting the speed to -1 (let SUMO control it)
            traci.vehicle.setSpeed('v1', -1.0)
            is_stopping = False
            has_stopped = True
            print(f"Vehicle v1 resuming normal driving at time {current_time}")

        # Get the current speed
        vehicle_speed = traci.vehicle.getSpeed('v1')
        total_speed = total_speed + vehicle_speed

    print(f"Time: {current_time:.2f} s, Vehicle speed: {vehicle_speed:.2f} m/s")

# Step 9: Close connection between SUMO and Traci
traci.close()