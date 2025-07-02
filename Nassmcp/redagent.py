
import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("RedAgentHub")  
@fast.agent(name="Red Agent",
            servers=["streamable_http_server"],
            instruction="""You are a Red Agent in a simulation environment.Your role is to provide attacks by calling the tools needed ."""
)
async def main():

    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
