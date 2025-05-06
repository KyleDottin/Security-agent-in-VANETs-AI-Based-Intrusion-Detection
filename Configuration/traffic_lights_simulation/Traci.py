# Step 1: Import required modules
import os
import sys

# Step 2: Set SUMO_HOME path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Import TraCI
import traci

# Step 4: Define SUMO configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'traci.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Step 5: Start SUMO
traci.start(Sumo_config)

# Step 6: Initialize variables
vehicle_ids = ['v0', 'v1', 'v2']
total_speed = {vid: 0 for vid in vehicle_ids}
vehicle_count = {vid: 0 for vid in vehicle_ids}

# Correct traffic light ID from net.xml
traffic_light_id = "J2"

# Step 7: Run simulation loop
try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        for vid in vehicle_ids:
            if vid in traci.vehicle.getIDList():
                speed = traci.vehicle.getSpeed(vid)
                total_speed[vid] += speed
                vehicle_count[vid] += 1
                print(f"{vid} speed: {speed:.2f} m/s")

                if vid in ['v0', 'v1']:
                    edge_id = traci.vehicle.getRoadID(vid)
                    if edge_id in ['E1', '-E0', ':J2_1', ':J2_2']:  # Optional: refine conditions
                        light_state = traci.trafficlight.getRedYellowGreenState(traffic_light_id)
                        print(f"Traffic Light {traffic_light_id} state: {light_state}")

finally:
    traci.close()
    print("Simulation finished.")

    # Print average speeds
    for vid in vehicle_ids:
        if vehicle_count[vid] > 0:
            avg_speed = total_speed[vid] / vehicle_count[vid]
            print(f"Average speed of {vid}: {avg_speed:.2f} m/s")
