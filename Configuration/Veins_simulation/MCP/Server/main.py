#!/usr/bin/env python3
"""
MCP Server for VANET Security Simulation
Compatible with current MCP library
"""

import asyncio
import json
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
    type: str
    position: Dict[str, float]  # x, y coordinates
    speed: float
    route: List[str]
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

# Create the server instance
server = Server("vanet-security-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="create_vehicle",
            description="Create a new vehicle in the VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "description": "Unique identifier for the vehicle"},
                    "vehicle_type": {"type": "string", "description": "Type of vehicle (car, truck, bus, etc.)"},
                    "position_x": {"type": "number", "description": "X coordinate position"},
                    "position_y": {"type": "number", "description": "Y coordinate position"},
                    "speed": {"type": "number", "description": "Initial speed of the vehicle", "default": 0.0},
                    "route": {"type": "array", "items": {"type": "string"}, "description": "List of road segments",
                              "default": []}
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
            description="Get the current status of the VANET simulation",
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
        types.Tool(
            name="start_simulation",
            description="Start the VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="stop_simulation",
            description="Stop the VANET simulation",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="reset_simulation",
            description="Reset the VANET simulation to initial state",
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
        if name == "create_vehicle":
            result = await create_vehicle(**arguments)
        elif name == "simulate_attack":
            result = await simulate_attack(**arguments)
        elif name == "get_simulation_status":
            result = await get_simulation_status()
        elif name == "detect_intrusion":
            result = await detect_intrusion(**arguments)
        elif name == "start_simulation":
            result = await start_simulation()
        elif name == "stop_simulation":
            result = await stop_simulation()
        elif name == "reset_simulation":
            result = await reset_simulation()
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        error_result = {"success": False, "error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def create_vehicle(
        vehicle_id: str,
        vehicle_type: str,
        position_x: float,
        position_y: float,
        speed: float = 0.0,
) -> Dict[str, Any]:
    """Create a new vehicle in the VANET simulation."""
    try:
        if vehicle_id in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Vehicle {vehicle_id} already exists"
            }

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            type=vehicle_type,
            position={"x": position_x, "y": position_y},
            speed=speed,
            route=route or []
        )

        simulation_state.vehicles[vehicle_id] = vehicle

        logger.info(f"Created vehicle {vehicle_id} at position ({position_x}, {position_y})")

        return {
            "success": True,
            "vehicle": vehicle.dict(),
            "message": f"Vehicle {vehicle_id} created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating vehicle: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def simulate_attack(
        attack_id: str,
        attack_type: str,
        target_vehicle_id: str,
        description: str,
        severity: int = 5
) -> Dict[str, Any]:
    """Simulate a security attack in the VANET."""
    try:
        if target_vehicle_id not in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Target vehicle {target_vehicle_id} does not exist"
            }

        attack = AttackScenario(
            attack_id=attack_id,
            attack_type=attack_type,
            target_vehicle_id=target_vehicle_id,
            description=description,
            severity=min(max(severity, 1), 10)  # Clamp to 1-10
        )

        simulation_state.active_attacks[attack_id] = attack

        # Mark target vehicle as under attack
        simulation_state.vehicles[target_vehicle_id].is_malicious = True

        logger.info(f"Simulated {attack_type} attack on vehicle {target_vehicle_id}")

        return {
            "success": True,
            "attack": attack.dict(),
            "message": f"Attack {attack_id} simulated successfully"
        }

    except Exception as e:
        logger.error(f"Error simulating attack: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_simulation_status() -> Dict[str, Any]:
    """Get the current status of the VANET simulation."""
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
        return {
            "success": False,
            "error": str(e)
        }


async def detect_intrusion(vehicle_id: str) -> Dict[str, Any]:
    """Run intrusion detection on a specific vehicle."""
    try:
        if vehicle_id not in simulation_state.vehicles:
            return {
                "success": False,
                "error": f"Vehicle {vehicle_id} does not exist"
            }

        vehicle = simulation_state.vehicles[vehicle_id]

        # Simple intrusion detection logic
        is_malicious = vehicle.is_malicious
        threat_level = "HIGH" if is_malicious else "LOW"

        # Check if vehicle is involved in any active attacks
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
        return {
            "success": False,
            "error": str(e)
        }


async def start_simulation() -> Dict[str, Any]:
    """Start the VANET simulation."""
    try:
        simulation_state.is_running = True
        simulation_state.simulation_time = 0.0

        logger.info("VANET simulation started")

        return {
            "success": True,
            "message": "Simulation started successfully",
            "simulation_time": simulation_state.simulation_time
        }

    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def stop_simulation() -> Dict[str, Any]:
    """Stop the VANET simulation."""
    try:
        simulation_state.is_running = False

        logger.info("VANET simulation stopped")

        return {
            "success": True,
            "message": "Simulation stopped successfully",
            "final_simulation_time": simulation_state.simulation_time
        }

    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def reset_simulation() -> Dict[str, Any]:
    """Reset the VANET simulation to initial state."""
    try:
        global simulation_state
        simulation_state = SimulationState()

        logger.info("VANET simulation reset")

        return {
            "success": True,
            "message": "Simulation reset successfully"
        }

    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def main():
    """Main entry point for the MCP server."""
    # Import here to avoid issues with event loop
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