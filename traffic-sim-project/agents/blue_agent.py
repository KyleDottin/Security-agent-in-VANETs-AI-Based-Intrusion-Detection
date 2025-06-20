import asyncio
import logging
from mcp_agent.core.fastagent import FastAgent

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

fast = FastAgent("blue_agent")

@fast.agent(
    instruction="""
You are a traffic simulation monitoring agent.
Your role is to monitor and control the traffic simulation.
You can:
1. Check the simulation state
2. Start/stop the simulation
3. Add/remove vehicles
4. Get the list of vehicles
Use these capabilities to help manage the traffic simulation.
""",
    servers=["mylocal"]
)
async def traffic_monitor(agent):
    try:
        logger.info("Traffic monitor agent started...")
        logger.debug(f"Agent methods: {dir(agent)}")

        async def call_tool_with_retry(server_name, tool_name, arguments, max_retries=3):
            for attempt in range(max_retries):
                try:
                    result = await agent.send(
                        server_name,
                        {
                            "jsonrpc": "2.0",
                            "method": "toolCall",
                            "params": {
                                "name": tool_name,
                                "parameters": arguments
                            },
                            "id": attempt + 1
                        }
                    )
                    return result.get("result", result)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {tool_name}: {e}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to call {tool_name} after {max_retries} attempts: {e}")
                    await asyncio.sleep(1)

        state = await call_tool_with_retry(
            server_name="mylocal",
            tool_name="get_simulation_state",
            arguments={}
        )
        logger.info(f"Current simulation state: {state}")

        if not state.get("running", False):
            start_result = await call_tool_with_retry(
                server_name="mylocal",
                tool_name="start_simulation",
                arguments={}
            )
            logger.info(f"Started simulation: {start_result}")

        return {
            "status": "success",
            "message": "Traffic monitor initialized",
            "state": state
        }

    except Exception as e:
        logger.error(f"Error in traffic monitor: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def main():
    try:
        logger.info("🚀 Starting Blue Agent...")
        
        async with fast.run() as session:
            logger.info("Agent session started")
            result = await traffic_monitor(session)
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