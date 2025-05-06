import os
import sys

# Setup SUMO environment
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# SUMO configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'traci.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Start SUMO
traci.start(Sumo_config)

# Initialize variables
vehicle_ids = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6']  # Updated vehicle IDs
total_speed = {vid: 0 for vid in vehicle_ids}
vehicle_count = {vid: 0 for vid in vehicle_ids}

traffic_light_id = "J2"  # Updated traffic light ID

# Custom green light phase (GGgrrrGGgrrr = allow traffic from specific directions)
green_phase = "GGgrrrGGgrrr"  # Updated green phase to match the traffic light configuration

# How many steps to force green light
green_duration = 100  # Adjust this value as needed
step = 0

try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1

        # Force green light for the first X steps
        if step <= green_duration:
            traci.trafficlight.setRedYellowGreenState(traffic_light_id, green_phase)
            print(f"[Step {step}] Traffic light set to: {green_phase}")
        else:
            # Let SUMO resume normal traffic light control
            print(f"[Step {step}] Default traffic light control resumes")

        for vid in vehicle_ids:
            if vid in traci.vehicle.getIDList():
                speed = traci.vehicle.getSpeed(vid)
                total_speed[vid] += speed
                vehicle_count[vid] += 1
                print(f"{vid} speed: {speed:.2f} m/s")

finally:
    traci.close()
    print("Simulation finished.")
    for vid in vehicle_ids:
        if vehicle_count[vid] > 0:
            avg_speed = total_speed[vid] / vehicle_count[vid]
            print(f"Average speed of {vid}: {avg_speed:.2f} m/s")
