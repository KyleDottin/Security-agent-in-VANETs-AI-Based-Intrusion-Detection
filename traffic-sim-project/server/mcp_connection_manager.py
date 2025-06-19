# mcp_connection_manager.py

class MCPConnectionManager:
    def __init__(self, get_simulation_data):
        """
        Initialize the MCPConnectionManager with a function to retrieve simulation data.

        :param get_simulation_data: A callable that returns the current simulation data.
        """
        self.get_simulation_data = get_simulation_data

    def handle_request(self, mcp_message):
        """
        Handle an incoming MCP message by processing it with the current simulation data.

        :param mcp_message: The incoming message to process.
        :return: Processed response based on the simulation data.
        """
        sim_data = self.get_simulation_data()
        # Process the MCP message with the simulation data
        # For now, just return the simulation data as a placeholder
        return {
            "status": "success",
            "simulation_data": sim_data,
            "message": mcp_message
        }
