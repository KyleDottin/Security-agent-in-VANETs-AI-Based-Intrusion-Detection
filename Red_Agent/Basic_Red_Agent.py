import random
import time
from uxsim import *
from IPython.display import display, Image

# Initialize simulation world
W = World(
    name="ddos_demo",  # Scenario name
    deltan=5,  # Simulation aggregation unit
    tmax=1200,  # Total simulation time
    print_mode=1,  # Print simulation progress
    save_mode=1,  # Save results
    show_mode=1,  # Show visualization
    random_seed=0  # Set random seed for repeatability
)

# Create nodes
W.addNode("orig1", 0, 0)
W.addNode("orig2", 0, 2)
node_signal = W.addNode("merge", 1, 1, signal=[30, 60])  # Add signal phases
W.addNode("dest", 2, 1)

# Add links and assign signal groups for dynamic traffic light
W.addLink("link1", "orig1", "merge", length=1000, free_flow_speed=20,
          number_of_lanes=1, merge_priority=0.5, signal_group=0)
W.addLink("link2", "orig2", "merge", length=1000, free_flow_speed=20,
          number_of_lanes=1, merge_priority=2, signal_group=1)
W.addLink("link3", "merge", "dest", length=1000, free_flow_speed=20,
          number_of_lanes=1)

# Define demand
W.adddemand("orig1", "dest", 0, 1000, 1)
W.adddemand("orig2", "dest", 500, 1000, 2)


# DDoS Red Agent Simulation: Flooding with irrelevant requests
def red_agent_ddos():
    """Simulate a DDoS attack by flooding the system with fake requests."""
    if int(W.TIME) % 50 == 0:  # Every 50 seconds simulate a DDoS attack
        num_requests = random.randint(10, 100)  # Simulate a random number of fake requests
        for _ in range(num_requests):
            random_link = random.choice(list(W.LINKS))  # Correctly pick a random link from LINK values
            random_phase = random.choice([0, 1])  # Randomly pick a signal phase (0 or 1)

            # Simulating DDoS: Randomly assign the signal group phase to disrupt normal flow
            if hasattr(random_link, 'signal_group'):
                random_link.signal_group = random_phase  # Alter signal group phase

            print(
                f"Red agent DDoS at t = {W.TIME}: Attacking signal phase on {random_link.name}, new phase = {random_phase}")


# Execute simulation in steps for dynamic signal logic
while W.check_simulation_ongoing():
    W.exec_simulation(duration_t2=10)  # Advance simulation by 10s

    # DDoS attack initiated by the red agent
    red_agent_ddos()

    # Display simulation status every 100 seconds
    if int(W.TIME) % 100 == 0:
        print(f"t = {W.TIME} s; Signal phase = {node_signal.signal_phase}")

# Visualization
W.analyzer.network_fancy(animation_speed_inverse=15, sample_ratio=0.3,
                         interval=3, trace_length=3, network_font_size=0)

with open("outddos_demo/anim_network_fancy.gif", "rb") as f:
    display(Image(data=f.read(), format='png'))

# Export analysis data
display(W.analyzer.basic_to_pandas())
display(W.analyzer.od_to_pandas())
display(W.analyzer.mfd_to_pandas())
display(W.analyzer.link_to_pandas())
display(W.analyzer.link_traffic_state_to_pandas())
display(W.analyzer.vehicles_to_pandas())

W.analyzer.output_data()
