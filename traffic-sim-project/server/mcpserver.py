import asyncio
from mcp_agent.core.fastagent import FastAgent
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import threading

# Initialize FastAgent
fast = FastAgent("Server Agent")

# Initialize FastAPI app
app = FastAPI(title="API-Agent-Server", description="Provides API access to VANET security agent")

# Shared agent instance
agent_app = None

@fast.agent(instruction="You are an API agent")
async def setup_agent():
    global agent_app
    async with fast.run() as agent:
        agent_app = agent
        # Keep the agent context alive
        while True:
            await asyncio.sleep(3600)

# Define the /api/detect POST endpoint
@app.post("/api/detect")
async def detect_intrusion(request: Request):
    global agent_app
    if not agent_app:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Get JSON payload
        data = await request.json()
        instruction = data.get("instruction")
        packet_data = data.get("data", {})
        
        # Send data to FastAgent for processing (placeholder interaction)
        response = await agent_app.send(f"Instruction: {instruction}, Data: {packet_data}")
        
        # Construct response
        return JSONResponse({
            "status": "success",
            "received_instruction": instruction,
            "packet_data": packet_data,
            "is_suspicious": False,  # Placeholder; replace with AI model logic
            "agent_response": response,
            "message": "Traffic analyzed successfully"
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

async def run_fastapi():
    # Run FastAPI server with Uvicorn
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Start FastAgent and FastAPI concurrently
    fastapi_task = asyncio.create_task(run_fastapi())
    agent_task = asyncio.create_task(setup_agent())
    await asyncio.gather(fastapi_task, agent_task)

if __name__ == "__main__":
    asyncio.run(main())