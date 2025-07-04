import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("StateTransfer")


@fast.agent(name="Blue Agent",
            servers=["streamable_http_server"],
            instruction="Monitor the SUMO simulation and provide updates on vehicle counts, traffic light states, or simulation statistics when asked. Can create vehicle too."
            )
@fast.agent(name="Red Agent",
            servers=["streamable_http_server"],
            instruction="Initiate attacks in the SUMO simulation, such as adding vehicles or simulating attacks, and request updates from the Blue Agent."
            )
# Define a chain workflow
@fast.chain(
    name="Adversarial agent",
    sequence=["Red Agent", "Blue Agent"],
    instruction="Execute Red Agent to generate a prompt and pass it to Blue Agent for response.",
    cumulative=False
)
async def adversarial_agent(agent):
    try:
        red_response = await agent.call_tool("Red Agent", "adversarial_attack", {})
        if "error" in red_response:
            return {"error": red_response["error"]}

        # Pass the prompt to Blue Agent
        blue_response = await agent.call_tool("Blue Agent", None, {"message": red_response})
        return {
            "red_agent_prompt": red_response,
            "blue_agent_response": blue_response
        }
    except Exception as e:
        return {"error": str(e)}

async def main():
    async with fast.run() as agent:

        try:
            # Start interactive session
            await agent.interactive()
        except KeyboardInterrupt:
            print("Interactive session terminated.")
        except Exception as e:
            print(f"Error in interactive session: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())