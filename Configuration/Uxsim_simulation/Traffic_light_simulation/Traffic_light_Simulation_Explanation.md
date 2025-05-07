
# Traffic light Simulation Explanation

This traffic ligth simulation add a dynamic traffic light that switches to green for the signal phase with the most vehicles waiting, aiming to reduce congestion at the intersection.


## Data Analysis and Visualization

After the simulation is complete, various analyses are conducted.
The simulation outputs a gif of the network animation and several CSV data files containing detailed traffic data. These files are stored in the directory `outtraffic_light_demo/`.

## Analysis of the Output

The output of the simulation includes several insights into traffic behavior:

- **Network Visualization**:
  - The animation helps visualize how traffic moves through the network.

- **Traffic Flow**:
  - The `df` dataframes contain the traffic flow for each origin-destination pair, link, and vehicle. Key metrics such as vehicle speed (`v`), flow (`q`), and density (`k`) are available for analysis.

- **Congestion and Merge Behavior**:
  - By analyzing the link-level data, you can see how traffic behaves at different points in the network.

- **Demand Impact**:
  - The simulation tracks how different demand levels from `orig1` and `orig2` affect the network.

## Running the Simulation

To run the simulation:
1. Install the **uxsim** package if you haven't already.
2. Copy the provided code into your Python environment (e.g., Jupyter Notebook).
3. Execute the code, and view the results as described above.
