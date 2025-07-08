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

5. **Access All Tools**
   - Once both the MCP server and your agent are running, you can access all available simulation tools from your LLM agent.

---

**Note:**
- Make sure your simulation files (network, routes, config) are correctly referenced in `MCP_server.py`.
- The server exposes endpoints for launching SUMO, creating vehicles, simulating attacks, and more.
- For best results, always activate your Python virtual environment before running the server or agent.

---

**How to Generate Random Vehicle Trips for the Map**

To change the number of vehicles in your map scenario, use the following command (adjust parameters as needed):

```bash
python "C:\Program Files (x86)\Eclipse\Sumo\tools\randomTrips.py" \
  -n map.net.xml \
  -r map.rou.xml \
  -b 0 \
  -e 1000 \
  -p 0.5 \
  --seed 42 \
  --validate \
  --vehicle-class passenger
```

- `-n map.net.xml` : Network file
- `-r map.rou.xml` : Output route file
- `-b 0` : Begin time (seconds)
- `-e 1000` : End time (seconds)
- `-p 0.5` : Probability of vehicle departure (lower = fewer vehicles)
- `--seed 42` : Random seed for reproducibility
- `--validate` : Validate generated trips
- `--vehicle-class passenger` : Type of vehicles

Adjust `-e` and `-p` to control the number and frequency of vehicles.

