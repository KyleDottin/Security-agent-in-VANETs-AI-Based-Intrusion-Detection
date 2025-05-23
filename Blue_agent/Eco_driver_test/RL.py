import os
import sys
import numpy as np
import pandas as pd
from sumolib import checkBinary
from gym import spaces
import traci
import math
import gym
import ollama
from langchain_openai import ChatOpenAI
from typing import Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime












types = "Conv"
os.makedirs("Results", exist_ok=True)
simulation_name = "NTT_Conv_Results.csv"
sim = "C:/Users/nanem/Downloads/Ecodriver/osm.sumocfg"
drl = "C:/Users/nanem/Downloads/Ecodriver/osm1.sumocfg"
total_simulation_time = 9000
# Global Variables
bus_stop = []
ids = []
no_use = []
speed_profiles = []
traffic_data = []
actual_data = []
unequipped_data = []
gather1 = []
gather2 = []
gather3 = []
conv_equipped = []
index = 0

# Physical Constants
g = 9.81  # Gravitational acceleration (m/s^2)
rho = 1.225  # Air density at 15°C (kg/m^3)
H_d = 36e6  # Diesel energy content (J/L)
rho_diesel = 0.832  # Diesel density (kg/L)
k_h = 0.5  # Heating coefficient (kW/°C)
k_c = 0.6  # Cooling coefficient (kW/°C)
T_int = 20  # Interior temperature (°C)
passenger_mass = 65  # Average passenger mass (kg)
P_base_idle = 7000  # Baseline idling power for diesel bus (W)
C_r = 0.01  # Rolling resistance coefficient

# Bus Parameters: (mass, efficiency, drag coefficient, frontal area)
params = {"Conv": (11200, 0.9, 0.72, 8.42)}

# Force and Power Calculation Functions
def rolling_resistance(M_v, M_p, C_r):
    """Calculate rolling resistance force (N)."""
    return C_r * (M_v + M_p) * g

def aerodynamic_drag(v, T_amb, C_d, A):
    """Calculate aerodynamic drag force (N), adjusting air density for temperature."""
    rho_adjusted = rho * (288.15 / (T_amb + 273.15))
    return 0.5 * rho_adjusted * C_d * A * v**2

def grade_force(M_v, M_p, slope_deg):
    """Calculate gravitational force due to slope (N)."""
    theta = math.radians(slope_deg)
    return (M_v + M_p) * g * math.sin(theta)

def acceleration_force(M_v, M_p, a):
    """Calculate acceleration force (N)."""
    return (M_v + M_p) * a

def auxiliary_power(T_amb):
    """Calculate auxiliary power for HVAC (W), based on ambient temperature."""
    return k_h * (T_int - T_amb) * 1000 if T_amb < T_int else k_c * (T_amb - T_int) * 1000

# Bus Consumption Models
def diesel_bus_consumption(v, num_passengers, slope_deg, T_amb, a, bus_type="Conv"):
    """Calculate diesel bus fuel consumption rate (kg/s)."""
    M_v, eta_ICE, C_d, A = params[bus_type]
    M_p = num_passengers * passenger_mass
    P_aux = auxiliary_power(T_amb)
    
    if v > 0 and a >= 0:
        F_roll = rolling_resistance(M_v, M_p, C_r)
        F_drag = aerodynamic_drag(v, T_amb, C_d, A)
        F_grade = grade_force(M_v, M_p, slope_deg)
        F_acc = acceleration_force(M_v, M_p, a)
        P_tractive = (F_roll + F_drag + F_grade + F_acc) * v
        P_total = max(P_tractive, 0) + P_aux
    else:
        P_total = P_base_idle + P_aux
    
    V_dot = P_total / (eta_ICE * H_d)  # L/s
    return V_dot * rho_diesel  # kg/s


def return_actual_data(stepss, sumo_config, initial_speed, road_speed_limit, slope, Temperature, passengers, distance, queue_number, phases_times, current_phase, current_phase_time):
    """Simulate and return actual energy consumption and travel time."""
    traci.start(["sumo", "-c", sumo_config, "--no-step-log"], label="Sim1")
    traci.switch("Sim1")
    step, energy, tt, energy11, energy22 = 0, 0, 0, 0, 0
    energy1 = 0.0
    fuel_consumption = 0.0
    while True:
        traci.simulationStep()
        if step == 0:
            traci.vehicle.add("veh0", "r_0", typeID='bus', depart='now', departLane='first', departPos='0', departSpeed=str(initial_speed/3.6))
            d = 300 if phases_times[0] != 10000000000000 else distance
            traci.edge.setMaxSpeed("E0", road_speed_limit/3.6)
            traci.edge.setMaxSpeed("E1", road_speed_limit/3.6)
            traci.edge.setMaxSpeed("E2", road_speed_limit/3.6)
            traci.lane.setLength("E0_0", d)
            traci.route.add("r1", ["E0", "E4"])
            tls_id = "J1"
            phases = [
                traci.trafficlight.Phase(phases_times[0], "GGrr", 0, phases_times[0]*1000),
                traci.trafficlight.Phase(phases_times[1], "yyrr", 0, phases_times[1]*3),
                traci.trafficlight.Phase(phases_times[2], "rrGG", 0, phases_times[2]*1000),
                traci.trafficlight.Phase(phases_times[3], "rryy", 0, phases_times[3]*3)
            ]
            logic = traci.trafficlight.Logic(programID="custom_program", type=0, currentPhaseIndex=current_phase, phases=phases)
            traci.trafficlight.setProgramLogic(tls_id, logic)
            traci.trafficlight.setPhaseDuration(tls_id, current_phase_time)
            for i in range(queue_number):
                traci.vehicle.add(str(i), "r1", "passenger", departPos=str(300 - (6 * i)))
        
        
        if traci.vehicle.getIDCount():
            slope_deg = math.degrees(math.atan(slope / 100))
            speed = traci.vehicle.getSpeed("veh0")
            accel = traci.vehicle.getAcceleration("veh0")
            fuel_consumption = diesel_bus_consumption(speed, passengers, slope_deg, Temperature, accel, "Conv")
            energy += float(fuel_consumption)

        tt += round(traci.inductionloop.getVehicleData("det1")[0][2], 0) if traci.inductionloop.getVehicleData("det1") else 0
        unequipped_data.append({"step": stepss + step, "Conv Bus fuel": fuel_consumption})
        step += 1
        if traci.inductionloop.getVehicleData("det1"):
            break
    traci.close()

    print(energy)
    return -((0.7 * energy) + (0.3 * (tt + 1)))

@tool
def recommended_speed(data):
    """
    Provides Recommend optimal speed using reinforcement learning..
    This tool analyzes bus operational data to generate a sequence of speed adjustments that aim to minimize energy consumption and reduce travel time. 
    ** It takes into account factors like inputs as follow:
    - data [0] (int): Bus type (Conv: stands for conventional Diesel Bus, Elec: stands for Electric Bus, and PHEB: stands for Plugin Hybrid Electric Bus).
    - data [1] (float):current Bus speed in km/h
    - data [2] (float):Road speed limit in km/h.
    - data [3] (float): Road slope in gradient.
    - data [4] (float): Ambient temperature in °C.
    - data [5] (int): Number of passengers in passenger.
    - data [6] (float): Remaining distance to the bus sation or the traffic lights in meters. 
    - data [7] (int): Queue length in front of traffic light in vehicles. 
    - data [8] (list): Traffic light full program [first direction red time in seconds, first direction yellow time in seconds, second direction red time in seconds, second direction yellow time in seconds].
    - data [9] (int): Current phase index 1: first direction red light, or 2: first direction yellow light, or 3: secind direction red light or 4: second direction yellow light.
    - data [10] (int): Remaining traffic light phase time in seconds.
    ** output:
     - Provide a list of speed actions.

    **Full Context:**

    **Purpose:**
    The primary purpose of this tool is to assist bus drivers in making informed
    decisions about their speed, leading to improved fuel efficiency (or battery
    efficiency for electric buses) and reduced travel duration.
   
    Returns:
        speed_actions (list): The recommended speed pattern.
    """ 
    global gather1, gather2, gather3, conv_equipped
    type_idx, initial_speed, road_speed_limit, slope, Temperature, passengers, distance, queue_number, phases_times, current_phase, current_phase_time = data
    stepp = 1
    class SumoEnv(gym.Env):
        def __init__(self, sumo_config, max_steps=10000):
            super().__init__()
            self.sumo_config = sumo_config
            self.max_steps = max_steps
            self.step_count = 0
            self.type = ["Conv", "Elec", "PHEB"][type_idx]
            self.initial_speed = initial_speed / 3.6
            self.road_speed_limit = road_speed_limit / 3.6
            self.slope = slope
            self.temperature = Temperature
            self.passengers = passengers
            self.target_distance = distance
            self.queue_number = queue_number
            self.stepp = stepp
            self.action_space = spaces.Discrete(9)
            self.observation_space = spaces.Box(low=0, high=120, shape=(11,), dtype=np.float32)
            actual_data.append(return_actual_data(stepp, sumo_config, initial_speed, road_speed_limit, slope, Temperature, passengers, distance, queue_number, phases_times, current_phase, current_phase_time))
            traci.start(["sumo", "-c", self.sumo_config, "--no-step-log"], label="DRL")
            traci.switch("DRL")

        def step(self, action, steppp):
            traci.simulationStep()
            travel_time = energy = 0
            if traci.vehicle.getIDCount():
                if action in range(5):
                    traci.vehicle.slowDown("veh0", 2.5 - (0.5 * action), 1)
                else:
                    traci.vehicle.setAcceleration("veh0", -2.5 + (0.5 * action), 1)
                speed = traci.vehicle.getSpeed("veh0")
                accel = traci.vehicle.getAcceleration("veh0")
                slope_deg = math.degrees(math.atan(self.slope / 100))
                fuel_consumption = diesel_bus_consumption(speed, self.passengers, slope_deg, self.temperature, accel, "Conv")
                energy = float(fuel_consumption)
                gather1.append({"step": steppp + stepp, "Conv Bus fuel": fuel_consumption})
            travel_time = round(traci.inductionloop.getVehicleData("det1")[0][2], 0) if traci.inductionloop.getVehicleData("det1") else 0
            self.step_count += 1
            state = np.array([type_idx, self.initial_speed, self.road_speed_limit, self.slope, self.temperature, self.passengers, self.target_distance, self.queue_number, *phases_times, current_phase, current_phase_time])
            reward = (-(0.7 * energy + 0.3 * travel_time))
            done = bool(traci.inductionloop.getVehicleData("det1")) or self.step_count >= self.max_steps
                            # Define the CSV filename
            filename = 'energy_data.csv'
        ######################################################################
            # Get current timestamp
            timestamp = datetime.now()

            # Prepare the data for saving with timestamp
            new_data = pd.DataFrame({
                'timestamp': [timestamp],
                'energy': [energy]
            })

            # Check if the file already exists
            file_exists = os.path.isfile(filename)

            if file_exists:
                # If file exists, append the value without rewriting headers
                new_data.to_csv(filename, mode='a', header=False, index=False)
            else:
                # If file doesn't exist, create it with headers
                new_data.to_csv(filename, index=False)
    ######################################################################
            print(energy)
            return state, reward, done, {}

        def reset(self):
            traci.close()
            traci.start(["sumo", "-c", self.sumo_config, "--no-step-log"], label="DRL")
            traci.switch("DRL")
            self.step_count = 0
            traci.vehicle.add("veh0", "r_0", typeID='bus', depart='now', departLane='first', departPos='0', departSpeed=str(self.initial_speed))
            d = 300 if phases_times[0] != 10000000000000 else self.target_distance
            traci.edge.setMaxSpeed("E0", self.road_speed_limit)
            traci.edge.setMaxSpeed("E1", self.road_speed_limit)
            traci.edge.setMaxSpeed("E2", self.road_speed_limit)
            traci.lane.setLength("E0_0", d)
            traci.route.add("r1", ["E0", "E4"])
            tls_id = "J1"
            phases = [
                traci.trafficlight.Phase(phases_times[0], "GGrr", 0, phases_times[0]*1000),
                traci.trafficlight.Phase(phases_times[1], "yyrr", 0, phases_times[1]*3),
                traci.trafficlight.Phase(phases_times[2], "rrGG", 0, phases_times[2]*1000),
                traci.trafficlight.Phase(phases_times[3], "rryy", 0, phases_times[3]*3)
            ]
            logic = traci.trafficlight.Logic(programID="custom_program", type=0, currentPhaseIndex=current_phase, phases=phases)
            traci.trafficlight.setProgramLogic(tls_id, logic)
            traci.trafficlight.setPhaseDuration(tls_id, current_phase_time)
            for i in range(self.queue_number):
                traci.vehicle.add(str(i), "r1", "passenger", departPos=str(300 - (6 * i)))
            return np.array([type_idx, self.initial_speed, self.road_speed_limit, self.slope, self.temperature, self.passengers, self.target_distance, self.queue_number, *phases_times, current_phase, current_phase_time])

        def close(self):
            traci.close()

    env = SumoEnv(drl)
    q_table = np.zeros((101, 9))
    epsilon = 1.0
    best_reward1 = best_reward2 = best_reward3 = -np.inf
    best_actions = []

    for _ in range(100):
        state = env.reset()
        total_reward1 =  0
        done = False
        step_count = 0
        while not done:
            action = env.action_space.sample() if np.random.rand() < epsilon else np.argmax(q_table[int(np.clip(state[0], 0, 100))])
            best_actions.append(action)
            next_state, reward, done, _ = env.step(action, step_count)
            total_reward1 += reward
            # print(total_reward1)
            q_table[int(np.clip(state[0], 0, 100)), action] += 0.1 * (
                (reward) + 0.99 * np.max(q_table[int(np.clip(next_state[0], 0, 100))]) -
                q_table[int(np.clip(state[0], 0, 100)), action]
            )
            state = next_state
            step_count += 1
        epsilon = max(0.01, epsilon * 0.995)
        total_reward1 -= actual_data[0]
        if total_reward1 > best_reward1:
            conv_equipped = list(gather1)
            best_reward1 = total_reward1
        gather1.clear()


    env.close()
    for data, filename in [
        (unequipped_data, "unequipped_bus_energy.csv"), (conv_equipped, "conv_bus_energy.csv")
    ]:
        df = pd.DataFrame(data)
        df.to_csv(f"Results/{filename}", mode='a', index=False, header=not os.path.exists(f"Results/{filename}"))
        data.clear()

    return best_reward1, best_reward2, best_reward3

model = ChatOpenAI(model="qwen2.5:1.5b", api_key="ollama", base_url="http://127.0.0.1:11434/v1", temperature=0.7, top_p=0.7)
# prompt = PromptTemplate(input_variables=["input"], template=prompt_template)
tools = [recommended_speed]
# Define the graph
graph = create_react_agent(model, tools=tools)

def LLM(input):
    messages = graph.invoke(input, stream_mode="values")
    return ({"input": input,"Based on simulations using the provided input data, I recommend the following driving instructions to optimize travel time and reduce fuel consumption" : messages["messages"][-1].content,})


