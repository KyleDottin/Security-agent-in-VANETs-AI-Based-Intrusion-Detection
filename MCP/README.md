# MCP Server for SUMO/LLM Integration

Easily connect your LLM agent to a SUMO traffic simulation using this MCP server.

## Quick Start

1. **Configure Your Simulation**
   - Edit `MCP_server.py` to set the correct file paths and simulation parameters for your environment.

2. **Start the MCP Server**
   ```bash
   python MCP_server.py
   ```
   The server will be available at: [http://127.0.0.1:8000/mcp](http://127.0.0.1:8000/mcp)

   > **Tip:** For interactive debugging and inspection of your MCP server, use:
   > ```bash
   > npx @modelcontextprotocol/inspector
   > ```

3. **Activate Your Virtual Environment**
   ```bash
   # On Powershell
   .\.venv\Scripts\Activate.ps1
   # On Windows
   .venv\Scripts\activate
   # On Linux/Mac
   source .venv/bin/activate
   ```

4. **Launch The Agent**
   ```bash
   uv run blueagent.py
   ```
   or
   ```bash
   uv run redagent.py
   ```
- Make sure you have installed the right LLM in the config file.

5. **Tools**
   - Once both the MCP server and your agent are running, you can access all available simulation tools from your LLM agent.
   - To use the adversarial attack tool, first run the red agent. When the red agent provides a prompt, copy that prompt and send it to the blue agent for processing.

---

**Note:**
- Make sure your simulation files (network, routes, config) are correctly referenced in `MCP_server.py`.
- The server exposes endpoints for launching SUMO, creating vehicles, simulating attacks, and more.
- For best results, always activate your Python virtual environment before running the server or agent.

---


