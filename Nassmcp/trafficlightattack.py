import random
import time
import traci

@mcp.tool("Traffic Light Tampering Attack", description="Simulates an attack by forcing all lights of a random traffic light to red and yellow (blinking) for a short period, then all green. Assumes the simulation is already running and TraCI is connected.")
def simulate_attack(params: dict = None) -> dict:
    global traci_connection, attack_override
    try:
        if traci_connection is None:
            return {"error": "TraCI connection is not active. Start the simulation first."}

        # Get all available traffic light IDs
        tls_ids = traci.trafficlight.getIDList()
        if not tls_ids:
            return {"error": "No traffic lights found in the simulation."}

        # Choose a random traffic light
        target_tls = random.choice(tls_ids)

        attack_override = True  # Disable adaptive logic during attack

        # Duration of the blinking effect (in seconds)
        attack_duration = 10
        # Blinking period (red ↔ yellow) in seconds
        blink_period = 0.5
        # How many blinking steps
        num_blinks = int(attack_duration / blink_period / 2)

        for i in range(num_blinks):
            # Set all lights to red
            traci.trafficlight.setRedYellowGreenState(target_tls, "r" * len(traci.trafficlight.getRedYellowGreenState(target_tls)))
            traci.simulationStep()
            time.sleep(blink_period)

            # Set all lights to yellow
            traci.trafficlight.setRedYellowGreenState(target_tls, "y" * len(traci.trafficlight.getRedYellowGreenState(target_tls)))
            traci.simulationStep()
            time.sleep(blink_period)

        # Finally, set all lights to green
        traci.trafficlight.setRedYellowGreenState(target_tls, "G" * len(traci.trafficlight.getRedYellowGreenState(target_tls)))

        return {"status": f"Attack simulated: {target_tls} blinking red/yellow, then all green.", "target_tls": target_tls}

    except Exception as e:
        return {"error": str(e)}
    finally:
        attack_override = False