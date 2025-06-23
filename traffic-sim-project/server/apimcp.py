import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp_agent.core.fastagent import FastAgent

app = FastAPI()
fast = FastAgent("API Agent", parse_cli_args=False)

@fast.agent(instruction="You are a helpful API assistant")
async def setup_agent():
    pass

agent_app = None

@app.on_event("startup")
async def startup_event():
    global agent_app

    async def run_agent():
        global agent_app
        async with fast.run() as agent:
            agent_app = agent
            await asyncio.Event().wait()  # Ne bloque pas la boucle principale

    asyncio.create_task(run_agent())  # Lance en tâche de fond


@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "")

    if not agent_app:
        return JSONResponse({"error": "Agent not initialized"}, status_code=503)

    response = await agent_app.send(question)
    return {"response": response}

# To run: uvicorn apimcp:app --host 127.0.0.1 --port 8000  
# to test: Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask" `
# >>     -Method Post `
# >>     -ContentType "application/json" `
# >>     -Body '{"question": "Hello, assistant!"}'