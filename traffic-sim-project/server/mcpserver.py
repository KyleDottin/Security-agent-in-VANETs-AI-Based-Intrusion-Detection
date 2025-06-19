from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Traffic Simulation MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulation state
sim_state = {
    "running": False,
    "vehicles": [],
    "start_time": None,
    "status": "stopped"
}

# MCP endpoints
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol messages"""
    try:
        body = await request.json()
        logger.info(f"Received MCP request: {body}")

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "initialize":
            # Handle initialization
            result = {
                "protocolVersion": "2025-03-26",  # Match client protocol version
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                        "items": [
                            {
                                "name": "get_simulation_state",
                                "description": "Get the current state of the simulation",
                                "parameters": { "type": "object", "properties": {} },
                                "inputSchema": { "type": "object", "properties": {} }
                            },
                            {
                                "name": "start_simulation",
                                "description": "Start the traffic simulation",
                                "parameters": { "type": "object", "properties": {} },
                                "inputSchema": { "type": "object", "properties": {} }
                            },
                            {
                                "name": "stop_simulation",
                                "description": "Stop the traffic simulation",
                                "parameters": { "type": "object", "properties": {} },
                                "inputSchema": { "type": "object", "properties": {} }
                            }
                        ]
                    },
                    "resources": {},
                    "prompts": {},
                    "logging": {
                        "level": "info"
                    }
                },
                "serverInfo": {
                    "name": "Traffic Simulation MCP Server",
                    "version": "0.1.0"
                }
            }
        elif method == "toolCall":
            # Handle tool calls
            tool_name = params.get("name")
            tool_params = params.get("parameters", {})
            if tool_name == "get_simulation_state":
                result = get_simulation_state()
            elif tool_name == "start_simulation":
                result = start_simulation()
            elif tool_name == "stop_simulation":
                result = stop_simulation()
            else:
                logger.error(f"Tool not found: {tool_name}")
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                })
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "get_simulation_state",
                        "description": "Get the current state of the simulation",
                        "parameters": {"type": "object", "properties": {}},
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "start_simulation",
                        "description": "Start the traffic simulation",
                        "parameters": {"type": "object", "properties": {}},
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "stop_simulation",
                        "description": "Stop the traffic simulation",
                        "parameters": {"type": "object", "properties": {}},
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            }
        elif method == "prompts/list":
            result = {
                "prompts": []  # No prompts defined yet
            }
        elif method == "notifications/initialized":
            # Just acknowledge the notification
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        else:
            logger.warning(f"Unhandled method: {method}")
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unhandled method: {method}"
                }
            })

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result if result is not None else {}
        }
        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id if request_id is not None else None,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }
        return JSONResponse(content=error_response, status_code=500)

# Tool implementations
def get_simulation_state() -> Dict[str, Any]:
    """Get the current state of the traffic simulation"""
    global sim_state
    return {
        "running": sim_state["running"],
        "vehicleCount": len(sim_state["vehicles"]),
        "status": sim_state["status"],
        "time": sim_state["start_time"].isoformat() if sim_state["start_time"] else None
    }

def start_simulation() -> Dict[str, Any]:
    """Start the traffic simulation"""
    global sim_state
    sim_state["running"] = True
    sim_state["start_time"] = datetime.now()
    sim_state["status"] = "running"
    logger.info("Simulation started")
    return {"status": "success", "message": "Simulation started successfully"}

def stop_simulation() -> Dict[str, Any]:
    """Stop the traffic simulation"""
    global sim_state
    sim_state["running"] = False
    sim_state["status"] = "stopped"
    logger.info("Simulation stopped")
    return {"status": "success", "message": "Simulation stopped successfully"}

def add_vehicle(vehicle_id: str, vehicle_type: str) -> Dict[str, Any]:
    """Add a new vehicle to the simulation"""
    global sim_state
    vehicle = {
        "id": vehicle_id,
        "type": vehicle_type,
        "added_at": datetime.now().isoformat()
    }
    sim_state["vehicles"].append(vehicle)
    logger.info(f"Added vehicle: {vehicle}")
    return {"status": "success", "message": f"Vehicle {vehicle_id} added successfully"}

def remove_vehicle(vehicle_id: str) -> Dict[str, Any]:
    """Remove a vehicle from the simulation"""
    global sim_state
    sim_state["vehicles"] = [v for v in sim_state["vehicles"] if v["id"] != vehicle_id]
    logger.info(f"Removed vehicle: {vehicle_id}")
    return {"status": "success", "message": f"Vehicle {vehicle_id} removed successfully"}

def get_vehicle_list() -> List[Dict[str, Any]]:
    """Get a list of all vehicles in the simulation"""
    global sim_state
    return sim_state["vehicles"]

# Helper function to handle tool calls
async def handle_tool_call(tool_name: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls from both toolCall and tools/run methods"""
    if tool_name == "get_simulation_state":
        return get_simulation_state()
    elif tool_name == "start_simulation":
        return start_simulation()
    elif tool_name == "stop_simulation":
        return stop_simulation()
    else:
        raise ValueError(f"Tool not found: {tool_name}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
