import asyncio
import logging
from mcp_agent.core.fastagent import FastAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fast = FastAgent("blue_agent")

@fast.agent(
    instruction="You are a basic agent that monitors the MCP server status.",
    servers=["mylocal"]
)
async def status_monitor(agent):
    result = await agent.run(input="Get the server status using get_status tool.")
    return {"status": "success", "message": "Status monitor completed", "server_status": result}

async def main():
    try:
        logger.info("🚀 Starting Blue Agent...")
        async with fast.run() as session:
            logger.info("Agent session started")
            result = await status_monitor(session)
            print(f"📊 Result: {result}")
            print("Agent running... Press Ctrl+C to stop")
            await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("🛑 Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())