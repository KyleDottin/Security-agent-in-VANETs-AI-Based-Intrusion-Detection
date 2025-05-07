from uxsim import *
from IPython.display import display, Image

# Initialize simulation world
W = World(
    name="traffic_light_demo",    # New scenario name
    deltan=5,
    tmax=1200,
    print_mode=1, save_mode=1, show_mode=1,
    random_seed=0
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
W.adddemand("orig1", "dest", 0, 1000, 0.4)
W.adddemand("orig2", "dest", 500, 1000, 0.6)

# Execute simulation in steps for dynamic signal logic
while W.check_simulation_ongoing():
    W.exec_simulation(duration_t2=10)  # Advance simulation in 10s chunks

    # Count vehicles on each signal-controlled link
    vehicles_per_links = {}
    for l in node_signal.inlinks.values():
        vehicles_per_links[tuple(l.signal_group)] = l.num_vehicles

    max_vehicles_group = max(vehicles_per_links, key=vehicles_per_links.get)

    # Every 100 seconds, print traffic light status
    if int(W.TIME) % 100 == 0:
        print(f"t = {W.TIME} s;",
              "; ".join([f"phase {k[0]} - vehicles = {v}" for k, v in vehicles_per_links.items()]),
              f"; green → phase {max_vehicles_group[0]}")

    # Dynamically switch to green for the most congested link
    node_signal.signal_phase = max_vehicles_group[0]
    node_signal.signal_t = 0  # Reset signal timer

# Visualization
W.analyzer.network_fancy(animation_speed_inverse=15, sample_ratio=0.3,
                         interval=3, trace_length=3, network_font_size=0)

with open("outtraffic_light_demo/anim_network_fancy.gif", "rb") as f:
    display(Image(data=f.read(), format='png'))

# Export analysis
display(W.analyzer.basic_to_pandas())
display(W.analyzer.od_to_pandas())
display(W.analyzer.mfd_to_pandas())
display(W.analyzer.link_to_pandas())
display(W.analyzer.link_traffic_state_to_pandas())
display(W.analyzer.vehicles_to_pandas())

W.analyzer.output_data()
