import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("AdversarialHub")


if __name__ == "__main__":
    asyncio.run(main())

@fast.agent(name="Blue Agent",
            servers=["streamable_http_server"],
            instruction="Monitor the SUMO simulation and provide updates on vehicle counts, traffic light states, or simulation statistics when asked. Can create vehicle too."
)
@fast.agent(
    name="Red Agent",
    servers=["streamable_http_server"],
    instruction="Initiate attacks in the SUMO simulation, such as adding vehicles or simulating attacks, and request updates from the Blue Agent."
)
# Define a chain workflow
@fast.chain(
    name="Adversarial Agent",
    sequence=["Red Agent", "Blue Agent"],
    default=True,
)

async def main():
    async with fast.run() as agent:
        await agent.interactive()