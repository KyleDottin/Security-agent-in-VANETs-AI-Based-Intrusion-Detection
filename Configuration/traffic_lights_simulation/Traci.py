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

# Step 6: Define variables
total_speed = {'v0': 0, 'v1': 0, 'v2': 0}
vehicle_count = {'v0': 0, 'v1': 0, 'v2': 0}

# ID of the traffic light
traffic_light_id = "junction0"  # Remplace avec l'ID réel du feu

# Step 7: Run the simulation loop
try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        for vid in ['v0', 'v1', 'v2']:
            if vid in traci.vehicle.getIDList():
                speed = traci.vehicle.getSpeed(vid)
                total_speed[vid] += speed
                vehicle_count[vid] += 1
                print(f"{vid} speed: {speed:.2f} m/s")

                # Check traffic light if vehicle is v0 or v1
                if vid in ['v0', 'v1']:
                    edge_id = traci.vehicle.getRoadID(vid)
                    if edge_id.startswith(":") or "junction" in edge_id:
                        light_state = traci.trafficlight.getRedYellowGreenState(traffic_light_id)
                        print(f"Traffic Light {traffic_light_id} state: {light_state}")

finally:
    traci.close()
    print("Simulation finished.")

    # Print average speeds
    for vid in total_speed:
        if vehicle_count[vid] > 0:
            avg_speed = total_speed[vid] / vehicle_count[vid]
            print(f"Average speed of {vid}: {avg_speed:.2f} m/s")
