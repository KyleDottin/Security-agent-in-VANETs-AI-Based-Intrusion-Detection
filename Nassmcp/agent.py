
import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("MyMCPAgent")  # nom de l'agent
@fast.agent(name="MCP Agent",
            servers=["streamable_http_server"],
            instruction="""You are an AI agent specialized in SUMO (Simulation of Urban Mobility) traffic simulation and VANET (Vehicular Ad-hoc Network) security analysis.
Be fast, you just need to call the tools provided by the MCP server to perform your tasks.Be quick and efficient in your responses.
"""
)
async def main():

    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
