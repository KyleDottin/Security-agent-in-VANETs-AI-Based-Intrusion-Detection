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
    'sumo-gui',  # or 'sumo' for the headless version
    '-c', 'traci.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Start SUMO
traci.start(Sumo_config)

# Initialize variables
vehicle_ids = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6']  # Vehicle IDs
total_speed = {vid: 0 for vid in vehicle_ids}  # To accumulate vehicle speeds
vehicle_count = {vid: 0 for vid in vehicle_ids}  # To count how many steps each vehicle has data

traffic_light_id = "J2"  # Traffic light ID (ensure it matches the traffic light in your network)

# Custom green light phase (may need to adjust according to your network setup)
green_phase = "GGgrrrGGgrrr"  # Example of a green phase
green_duration = 100  # How long the forced green light lasts, in number of steps

max_steps = 1000  # Total number of simulation steps

try:
    for step in range(max_steps):
        traci.simulationStep()

        # Force green light for the first 'green_duration' steps
        if step <= green_duration:
            traci.trafficlight.setRedYellowGreenState(traffic_light_id, green_phase)
            print(f"[Step {step}] Traffic light set to: {green_phase}")
        else:
            # Let SUMO control the traffic light normally after the forced green period
            print(f"[Step {step}] Normal traffic light control resumed")

        # Track vehicle speeds and accumulate data
        for vid in vehicle_ids:
            if vid in traci.vehicle.getIDList():  # Check if the vehicle is in the simulation
                speed = traci.vehicle.getSpeed(vid)
                total_speed[vid] += speed
                vehicle_count[vid] += 1
                print(f"{vid} speed: {speed:.2f} m/s")

finally:
    traci.close()  # End the connection to SUMO
    print("Simulation finished.")
    for vid in vehicle_ids:
        if vehicle_count[vid] > 0:
            avg_speed = total_speed[vid] / vehicle_count[vid]
            print(f"Average speed of {vid}: {avg_speed:.2f} m/s")
