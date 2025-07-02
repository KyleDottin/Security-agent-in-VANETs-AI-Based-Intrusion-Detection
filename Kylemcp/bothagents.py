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
async def red_agent(agent):
    while True:
        # Receive user message
        message = await agent.receive()

        # Check message content
        if "adversarial attack" in message.content.lower():
            # Call the tool
            tool_result = await agent.call_tool("adversarial_attack")

            # Extract text
            if tool_result and len(tool_result.content) > 0:
                text = tool_result.content[0].text
                # Send the text back to the user
                await agent.send(text)
            else:
                await agent.send("The tool did not return any prompt.")
        else:
            await agent.send("Please type 'adversarial attack' to generate the prompt.")

async def main():

    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())