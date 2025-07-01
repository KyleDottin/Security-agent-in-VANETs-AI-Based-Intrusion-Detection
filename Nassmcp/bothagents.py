import asyncio
from mcp_agent.core.fastagent import FastAgent



fast = FastAgent("StateTransfer")
@fast.agent(name="Blue Agent",
            servers=["streamable_http_server"],
            instruction="""
Just use the tools provided by the MCP server to perform your tasks."""
)


@fast.agent(name="Red Agent",
            servers=["streamable_http_server"],
            instruction="""
Just use the tools provided by the MCP server to perform your tasks.
"""
)
async def main():

    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())