import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("AdversarialHub")


@fast.agent(
    name="Red Agent",
    servers=["streamable_http_server"],
    instruction="Initiate attacks in the SUMO simulation, such as adding vehicles or simulating attacks, and request updates from the Blue Agent.",
    default=True,
)

async def main():
    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())