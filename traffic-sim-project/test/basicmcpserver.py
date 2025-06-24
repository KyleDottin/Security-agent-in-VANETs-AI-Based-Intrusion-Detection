from fastmcp import FastMCP

# Initialise le serveur MCP
mcp = FastMCP("Demo")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool("Demarre simulation de trafic")
def start_traffic_simulation() -> dict:
    print("Le chat est noir")
    return {"started": True}

# Point d'entrée principal
if __name__ == "__main__":
    print("🚀 MCP running at http://127.0.0.1:8000/mcp")
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"  
    )
