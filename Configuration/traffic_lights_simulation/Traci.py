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

# Vehicle and traffic light setup
vehicle_ids = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6']
total_speed = {vid: 0 for vid in vehicle_ids}
vehicle_count = {vid: 0 for vid in vehicle_ids}
traffic_light_id = "J2"

# Phase to force (must match your network definition)
green_phase = "GGgrrrGGgrrr"  # Modify as per your actual light phase layout

# Lanes to monitor (adjust based on your .net.xml file)
incoming_lanes = ["E0_0", "E1_0", "E2_0", "E3_0"]

# Dynamic control thresholds
step = 0
force_green = False
green_force_duration = 50  # Number of steps to keep green once activated
green_force_counter = 0
vehicle_threshold = 5  # Trigger green if >= this many vehicles in queue

try:
    max_steps = 1000  # or however many simulation steps you want

    for step in range(max_steps):
        traci.simulationStep()

        if step <= green_force_duration:
            traci.trafficlight.setRedYellowGreenState(traffic_light_id, green_phase)
            print(f"[Step {step}] Traffic light set to: {green_phase}")
        else:
            print(f"[Step {step}] Default traffic light control resumes")

        for vid in vehicle_ids:
            if vid in traci.vehicle.getIDList():
                speed = traci.vehicle.getSpeed(vid)
                total_speed[vid] += speed
                vehicle_count[vid] += 1
                print(f"{vid} speed: {speed:.2f} m/s")


finally:
    traci.close()
    print("\nSimulation finished.")
    for vid in vehicle_ids:
        if vehicle_count[vid] > 0:
            avg_speed = total_speed[vid] / vehicle_count[vid]
            print(f"Average speed of {vid}: {avg_speed:.2f} m/s")
