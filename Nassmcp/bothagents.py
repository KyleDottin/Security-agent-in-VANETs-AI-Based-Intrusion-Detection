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

import asyncio
from mcp_agent.core.fastagent import FastAgent

# Initialize FastAgent
fast = FastAgent("AgentHub")

# Define Agent1
@fast.agent(name="agent1", instruction="You are Agent1, respond to messages from Agent2.")
async def agent1(message: str):
    return f"Agent1 received: {message}. How can I assist you?"

# Define Agent2
@fast.agent(name="agent2", instruction="You are Agent2, initiate conversation with Agent1.")
async def agent2(message: str):
    return f"Agent2 says: Hello, Agent1! Let's collaborate."

# Define conversation workflow
@fast.chain(name="conversation", sequence=["agent2", "agent1"])
async def conversation_workflow():
    async with fast.run() as agent:
        # Agent2 initiates
        response = await agent["agent2"].send("Start conversation")
        print(f"Agent2 response: {response}")
        # Agent1 responds
        reply = await agent["agent1"].send(response)
        print(f"Agent1 reply: {reply}")
        return reply

# Run the workflow
if __name__ == "__main__":
    asyncio.run(conversation_workflow())
