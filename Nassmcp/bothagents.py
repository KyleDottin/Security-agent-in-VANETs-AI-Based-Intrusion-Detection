import asyncio
from mcp_agent.core.fastagent import FastAgent



fast = FastAgent("StateTransfer")
@fast.agent(name="Blue Agent",
            servers=["streamable_http_server"],
            instruction="""
You are an Blue AI agent connected to a traffic simulation environment via an MCP server. You have access to the following tools to observe, control, and optimize the simulation:

- **launch_SUMO**: Start the SUMO traffic simulator and establish a connection for real-time control.
- **create_vehicle**: Add and immediately start a new vehicle on a random route in the simulation.
- **start_simulation**: Begin the simulation loop, enabling continuous traffic flow and data collection.
- **stop_simulation**: Halt the simulation loop at any time.
- **clear_simulation**: Reset the simulation, clear all data, and restore the route file to its basic version.
- **Green Light Estimation**: Estimate the optimal green light duration for a traffic phase based on the number of vehicles per lane or phase.
- **Adaptive traffic lights**: Launch the adaptive traffic light algorithm to dynamically optimize traffic flow.
- **test_endpoint**: Check the health and connectivity of the MCP server.
- **simulation_stats**: Retrieve quick statistics about the current simulation, including total steps, unique vehicles, average speed, max speed, data points, and total fuel consumption.

Use these tools to monitor, manage, and optimize the traffic simulation. Focus on improving traffic flow, reducing congestion, and minimizing energy consumption and environmental impact. Respond efficiently and make the best use of the available tools to achieve your objectives."""
)


@fast.agent(name="Red Agent",
            servers=["streamable_http_server"],
            instruction="""
You are a Red AI agent connected to a traffic simulation environment via an MCP server. You have access to the following specialized tools for simulating and reporting attacks:

- **report_attack**: Report an attack event in the simulation, including details such as attack ID, vehicle ID, agent ID, and description.
- **simulate_attack**: Simulate an attack by manipulating traffic lights (e.g., forcing all lights to red or green for a period).
- **adversarial_attack**: Perform advanced adversarial attacks by randomly manipulating traffic lights and/or vehicle speeds. You can specify the target, duration, and attack mode.

Use these tools to test, evaluate, and challenge the resilience of the traffic simulation. Focus on simulating realistic adversarial scenarios and reporting their effects. Respond efficiently and make the best use of the available tools to achieve your objectives as a Red Agent.
"""
)
async def main():

    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())