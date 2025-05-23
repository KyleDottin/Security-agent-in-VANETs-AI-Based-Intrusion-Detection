from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
# from veins_python import VeinsPythonBridge  # Import the Veins Python Bridge

load_dotenv()

class Settings(BaseSettings):
    server_script_path: str = r"C:\Users\tru89\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Configuration\Veins_simulation\MCP\Server\main.py"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MCPClient()
    try:
        connected = await client.connect_to_server(settings.server_script_path) #Connection to the server
        if not connected:
            raise HTTPException(
                status_code=500, detail="Failed to connect to MCP server"
            )
        app.state.client = client
        yield
    except Exception as e:
        print(f"Error during lifespan: {e}")
        raise HTTPException(status_code=500, detail="Error during lifespan") from e
    finally:
        await client.cleanup()

app = FastAPI(title="MCP Client API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

class Message(BaseModel):
    role: str
    content: Any

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

class Vehicle(BaseModel):
    vehicle_id: str
    vehicle_type: str
    make: str
    model: str
    position_x: float
    position_y: float
    speed: float = 0.0


class AttackReport(BaseModel):
    attack_id: str
    vehicle_id: str
    agent_id: str
    details: str

class SimulateAttack(BaseModel):
    attack_id: str

# Initialize the Veins Python Bridge
# veins_bridge = VeinsPythonBridge()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Simulation API"}

# Add an endpoint to process queries using the MCP client
@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        client = app.state.client
        messages = await client.process_query(request.query)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to create a vehicle
@app.post("/create_vehicle")
async def create_vehicle(vehicle: Vehicle):
    try:
        # Use the Veins Python Bridge to create a vehicle in the simulation
        # result = veins_bridge.create_vehicle(vehicle.vehicle_id, vehicle.type)
        return {"message": "Vehicle created successfully", "vehicle": vehicle}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to report an attack
@app.post("/report_attack")
async def report_attack(attack_report: AttackReport):
    try:
        # Use the Veins Python Bridge to report an attack in the simulation
        # result = veins_bridge.report_attack(attack_report.attack_id, attack_report.vehicle_id, attack_report.agent_id, attack_report.details)
        return {"message": "Attack reported successfully", "attack_report": attack_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to simulate an attack
@app.post("/simulate_attack")
async def simulate_attack(simulate_attack: SimulateAttack):
    try:
        # Use the Veins Python Bridge to simulate an attack in the simulation
        # result = veins_bridge.simulate_attack(simulate_attack.attack_id)
        return {"message": "Attack simulated successfully", "simulate_attack": simulate_attack}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# example of command : curl -X POST "http://localhost:8000/create_vehicle" -H "Content-Type: application/json" -d "{\"vehicle_id\":\"veh123\",\"vehicle_type\":\"car\",\"make\":\"Toyota\",\"model\":\"Corolla\",\"position_x\":100.5,\"position_y\":200.0,\"speed\":45.0}"

