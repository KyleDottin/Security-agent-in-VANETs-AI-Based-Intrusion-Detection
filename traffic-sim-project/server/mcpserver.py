import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("Server Agent")

@fast.agent(instruction="You are an API agent")
async def main():
    # Start as a server programmatically
    await fast.start_server(
        transport="http",
        host="127.0.0.1",
        port=8080,
        server_name="API-Agent-Server",
        server_description="Provides API access to my agent"
    )


if __name__ == "__main__":
    asyncio.run(main())