from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Basic MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server_state = {"status": "idle"}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
        logger.info(f"Received MCP request: {body}")

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                        "items": [
                            {
                                "name": "get_status",
                                "description": "Get the current status of the server",
                                "parameters": {"type": "object", "properties": {}},
                                "inputSchema": {"type": "object", "properties": {}}
                            }
                        ]
                    },
                    "resources": {},
                    "prompts": {},
                    "logging": {"level": "info"}
                },
                "serverInfo": {
                    "name": "Basic MCP Server",
                    "version": "0.1.0"
                }
            }
        elif method == "toolCall":
            tool_name = params.get("name")
            if tool_name == "get_status":
                result = server_state
            else:
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
                        "name": "get_status",
                        "description": "Get the current status of the server",
                        "parameters": {"type": "object", "properties": {}},
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            }
        elif method == "prompts/list":
            result = {"prompts": []}
        elif method == "notifications/initialized":
            logger.info("Received initialized notification")
            return Response(status_code=204)
        else:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)