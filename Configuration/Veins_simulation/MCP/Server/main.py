#!/usr/bin/env python3
"""
Enhanced MCP Server for VANET Security Simulation
Now includes integration with SUMO simulation via FastAPI
"""

import asyncio
import json
import httpx
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data models for your VANET simulation
class Vehicle(BaseModel):
    vehicle_id: str
    vehicle_type: str
    position: Dict[str, float]
    speed: float
    is_malicious: bool = False


class AttackScenario(BaseModel):
    attack_id: str
    attack_type: str
    target_vehicle_id: str
    description: str
    severity: int  # 1-10 scale


class SimulationState(BaseModel):
    vehicles: Dict[str, Vehicle] = {}
    active_attacks: Dict[str, AttackScenario] = {}
    simulation_time: float = 0.0
    is_running: bool = False


# Global simulation state
simulation_state = SimulationState()

# HTTP client for FastAPI communication
http_client = httpx.AsyncClient(timeout=30.0)
FASTAPI_BASE_URL = "http://localhost:8000"

# Create the server instance
server = Server("vanet-security-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        # Existing VANET security tools
        types.Tool(
            name="create_vehicle_memory",
            description="Create a new vehicle in the in-memory VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "description": "Unique identifier for the vehicle"},
                    "vehicle_type": {"type": "string", "description": "Type of vehicle (car, truck, bus, etc.)"},
                    "position_x": {"type": "number", "description": "X coordinate position"},
                    "position_y": {"type": "number", "description": "Y coordinate position"},
                    "speed": {"type": "number", "description": "Initial speed of the vehicle", "default": 0.0},
                },
                "required": ["vehicle_id", "vehicle_type", "position_x", "position_y"]
            }
        ),
        types.Tool(
            name="simulate_attack",
            description="Simulate a security attack in the VANET",
            inputSchema={
                "type": "object",
                "properties": {
                    "attack_id": {"type": "string", "description": "Unique identifier for the attack"},
                    "attack_type": {"type": "string", "description": "Type of attack (DoS, Sybil, Black Hole, etc.)"},
                    "target_vehicle_id": {"type": "string", "description": "ID of the vehicle being attacked"},
                    "description": {"type": "string", "description": "Description of the attack scenario"},
                    "severity": {"type": "integer", "description": "Severity level (1-10)", "default": 5}
                },
                "required": ["attack_id", "attack_type", "target_vehicle_id", "description"]
            }
        ),
        types.Tool(
            name="get_simulation_status",
            description="Get the current status of the in-memory VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="detect_intrusion",
            description="Run intrusion detection on a specific vehicle",
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "description": "ID of the vehicle to analyze"}
                },
                "required": ["vehicle_id"]
            }
        ),

        # New SUMO integration tools
        types.Tool(
            name="start_sumo",
            description="Start SUMO simulation and connect TraCI",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="start_sumo_simulation",
            description="Start the SUMO simulation loop",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="stop_sumo_simulation",
            description="Stop the SUMO simulation loop",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="create_sumo_vehicle",
            description="Create a new vehicle in the SUMO simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "description": "Unique identifier for the vehicle"},
                    "time_departure": {"type": "number", "description": "Departure time in seconds"},
                    "road_depart": {"type": "string", "description": "Starting road/edge ID"},
                    "road_arrival": {"type": "string", "description": "Destination road/edge ID"}
                },
                "required": ["vehicle_id", "time_departure", "road_depart", "road_arrival"]
            }
        ),
        types.Tool(
            name="get_sumo_stats",
            description="Get current SUMO simulation statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="query_sumo_analysis",
            description="Query the SUMO simulation data with AI analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query about the simulation"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="clear_sumo_simulation",
            description="Clear and reset the SUMO simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),

        # Original memory-based simulation controls
        types.Tool(
            name="start_memory_simulation",
            description="Start the in-memory VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="stop_memory_simulation",
            description="Stop the in-memory VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="reset_memory_simulation",
            description="Reset the in-memory VANET simulation to initial state",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        # SUMO integration tools
        if name == "start_sumo":
            result = await start_sumo()
        elif name == "start_sumo_simulation":
            result = await start_sumo_simulation()
        elif name == "stop_sumo_simulation":
            result = await stop_sumo_simulation()
        elif name == "create_sumo_vehicle":
            result = await create_sumo_vehicle(**arguments)
        elif name == "get_sumo_stats":
            result = await get_sumo_stats()
        elif name == "query_sumo_analysis":
            result = await query_sumo_analysis(**arguments)
        elif name == "clear_sumo_simulation":
            result = await clear_sumo_simulation()

        # Original memory-based tools
        elif name == "create_vehicle_memory":
            result = await create_vehicle_memory(**arguments)
        elif name == "simulate_attack":
            result = await simulate_attack(**arguments)
        elif name == "get_simulation_status":
            result = await get_simulation_status()
        elif name == "detect_intrusion":
            result = await detect_intrusion(**arguments)
        elif name == "start_memory_simulation":
            result = await start_memory_simulation()
        elif name == "stop_memory_simulation":
            result = await stop_memory_simulation()
        elif name == "reset_memory_simulation":
            result = await reset_memory_simulation()
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        error_result = {"success": False, "error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


# SUMO Integration Functions
async def start_sumo() -> Dict[str, Any]:
    """Start SUMO simulation via FastAPI"""
    try:
        response = await http_client.post(f"{FASTAPI_BASE_URL}/SUMO")
        result = response.json()
        return {"success": True, "sumo_status": result}
    except Exception as e:
        return {"success": False, "error": f"Error starting SUMO: {str(e)}"}


async def start_sumo_simulation() -> Dict[str, Any]:
    """Start SUMO simulation loop via FastAPI"""
    try:
        response = await http_client.post(f"{FASTAPI_BASE_URL}/start_simulation")
        result = response.json()
        return {"success": True, "simulation_status": result}
    except Exception as e:
        return {"success": False, "error": f"Error starting SUMO simulation: {str(e)}"}


async def stop_sumo_simulation() -> Dict[str, Any]:
    """Stop SUMO simulation loop via FastAPI"""
    try:
        response = await http_client.post(f"{FASTAPI_BASE_URL}/stop_simulation")
        result = response.json()
        return {"success": True, "simulation_status": result}
    except Exception as e:
        return {"success": False, "error": f"Error stopping SUMO simulation: {str(e)}"}


async def create_sumo_vehicle(vehicle_id: str, time_departure: float, road_depart: str, road_arrival: str) -> Dict[
    str, Any]:
    """Create vehicle in SUMO simulation via FastAPI"""
    try:
        vehicle_data = {
            "vehicle_id": vehicle_id,
            "time_departure": time_departure,
            "road_depart": road_depart,
            "road_arrival": road_arrival
        }
        response = await http_client.post(f"{FASTAPI_BASE_URL}/create_vehicle", json=vehicle_data)
        result = response.json()
        return {"success": True, "vehicle_creation": result}
    except Exception as e:
        return {"success": False, "error": f"Error creating SUMO vehicle: {str(e)}"}


async def get_sumo_stats() -> Dict[str, Any]:
    """Get SUMO simulation statistics via FastAPI"""
    try:
        response = await http_client.get(f"{FASTAPI_BASE_URL}/simulation_stats")
        result = response.json()
        return {"success": True, "stats": result}
    except Exception as e:
        return {"success": False, "error": f"Error getting SUMO stats: {str(e)}"}


async def query_sumo_analysis(query: str) -> Dict[str, Any]:
    """Query SUMO simulation with AI analysis via FastAPI"""
    try:
        query_data = {"query": query}
        response = await http_client.post(f"{FASTAPI_BASE_URL}/query", json=query_data)
        result = response.json()
        return {"success": True, "analysis": result}
    except Exception as e:
        return {"success": False, "error": f"Error querying SUMO analysis: {str(e)}"}


async def clear_sumo_simulation() -> Dict[str, Any]:
    """Clear SUMO simulation via FastAPI"""
    try:
        response = await http_client.post(f"{FASTAPI_BASE_URL}/clear")
        result = response.json()
        return {"success": True, "clear_status": result}
    except Exception as e:
        return {"success": False, "error": f"Error clearing SUMO simulation: {str(e)}"}


# Original VANET Security Functions (renamed to avoid confusion)
async def create_vehicle_memory(
        vehicle_id: str,
        vehicle_type: str,
        position_x: float,
        position_y: float,
        speed: float = 0.0
) -> Dict[str, Any]:
    """Create a new vehicle in the in-memory VANET simulation."""
    try:
        if vehicle_id in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Vehicle {vehicle_id} already exists in memory"
            }

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            position={"x": position_x, "y": position_y},
            speed=speed
        )

        simulation_state.vehicles[vehicle_id] = vehicle
        logger.info(f"Created vehicle {vehicle_id} in memory simulation")

        return {
            "success": True,
            "vehicle": vehicle.dict(),
            "message": f"Vehicle {vehicle_id} created in memory simulation"
        }

    except Exception as e:
        logger.error(f"Error creating vehicle in memory: {e}")
        return {"success": False, "error": str(e)}


# Keep all your existing functions but rename them to avoid confusion
async def simulate_attack(attack_id: str, attack_type: str, target_vehicle_id: str, description: str,
                          severity: int = 5) -> Dict[str, Any]:
    """Simulate a security attack in the VANET."""
    try:
        if target_vehicle_id not in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Target vehicle {target_vehicle_id} does not exist in memory simulation"
            }

        attack = AttackScenario(
            attack_id=attack_id,
            attack_type=attack_type,
            target_vehicle_id=target_vehicle_id,
            description=description,
            severity=min(max(severity, 1), 10)
        )

        simulation_state.active_attacks[attack_id] = attack
        simulation_state.vehicles[target_vehicle_id].is_malicious = True

        logger.info(f"Simulated {attack_type} attack on vehicle {target_vehicle_id}")

        return {
            "success": True,
            "attack": attack.dict(),
            "message": f"Attack {attack_id} simulated successfully"
        }

    except Exception as e:
        logger.error(f"Error simulating attack: {e}")
        return {"success": False, "error": str(e)}


async def get_simulation_status() -> Dict[str, Any]:
    """Get the current status of the in-memory VANET simulation."""
    try:
        return {
            "success": True,
            "status": {
                "vehicle_count": len(simulation_state.vehicles),
                "active_attack_count": len(simulation_state.active_attacks),
                "simulation_time": simulation_state.simulation_time,
                "is_running": simulation_state.is_running,
                "vehicles": [v.dict() for v in simulation_state.vehicles.values()],
                "active_attacks": [a.dict() for a in simulation_state.active_attacks.values()]
            }
        }
    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        return {"success": False, "error": str(e)}


async def detect_intrusion(vehicle_id: str) -> Dict[str, Any]:
    """Run intrusion detection on a specific vehicle."""
    try:
        if vehicle_id not in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Vehicle {vehicle_id} does not exist in memory simulation"
            }

        vehicle = simulation_state.vehicles[vehicle_id]
        is_malicious = vehicle.is_malicious
        threat_level = "HIGH" if is_malicious else "LOW"

        active_attacks = [
            attack for attack in simulation_state.active_attacks.values()
            if attack.target_vehicle_id == vehicle_id
        ]

        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "is_malicious": is_malicious,
            "threat_level": threat_level,
            "active_attacks": [attack.dict() for attack in active_attacks],
            "detection_timestamp": simulation_state.simulation_time
        }

    except Exception as e:
        logger.error(f"Error detecting intrusion: {e}")
        return {"success": False, "error": str(e)}


async def start_memory_simulation() -> Dict[str, Any]:
    """Start the in-memory VANET simulation."""
    try:
        simulation_state.is_running = True
        simulation_state.simulation_time = 0.0
        logger.info("In-memory VANET simulation started")
        return {
            "success": True,
            "message": "In-memory simulation started successfully",
            "simulation_time": simulation_state.simulation_time
        }
    except Exception as e:
        logger.error(f"Error starting memory simulation: {e}")
        return {"success": False, "error": str(e)}


async def stop_memory_simulation() -> Dict[str, Any]:
    """Stop the in-memory VANET simulation."""
    try:
        simulation_state.is_running = False
        logger.info("In-memory VANET simulation stopped")
        return {
            "success": True,
            "message": "In-memory simulation stopped successfully",
            "final_simulation_time": simulation_state.simulation_time
        }
    except Exception as e:
        logger.error(f"Error stopping memory simulation: {e}")
        return {"success": False, "error": str(e)}


async def reset_memory_simulation() -> Dict[str, Any]:
    """Reset the in-memory VANET simulation to initial state."""
    try:
        global simulation_state
        simulation_state = SimulationState()
        logger.info("In-memory VANET simulation reset")
        return {
            "success": True,
            "message": "In-memory simulation reset successfully"
        }
    except Exception as e:
        logger.error(f"Error resetting memory simulation: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Main entry point for the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vanet-security-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())