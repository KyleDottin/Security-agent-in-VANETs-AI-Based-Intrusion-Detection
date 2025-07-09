import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("AdversarialHub")


@fast.agent(name="Blue Agent",
            servers=["streamable_http_server"],
            instruction="Monitor the SUMO simulation and provide updates on vehicle counts, traffic light states, or simulation statistics when asked. Can create vehicle too."
)
async def blue_agent(agent):
    # Tool to handle generic prompts (including adversarial ones)
    @agent.tool("handle_prompt", description="Processes any prompt received from another agent and responds naturally.")
    async def handle_prompt(prompt_data: dict) -> dict:
        prompt = prompt_data.get("prompt", "")
        print(f"Blue Agent received prompt: {prompt}")
        await agent.process_query(prompt)

async def main():
    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())