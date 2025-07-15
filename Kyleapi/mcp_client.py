from typing import Optional
from contextlib import AsyncExitStack
import traceback
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from logger import *

load_dotenv()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.base_url = "http://localhost:11434/api/chat"
        self.tools = []
        self.messages = []
        self.logger = logger

    async def connect_to_server(self, server_script_path: str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command, args=[server_script_path], env=None
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()

            self.logger.info("Connected to MCP server")

            mcp_tools = await self.get_mcp_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools
            ]

            self.logger.info(
                f"Available tools: {[tool['name'] for tool in self.tools]}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error connecting to MCP server: {e}")
            traceback.print_exc()
            raise

    async def get_mcp_tools(self):
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            self.logger.error(f"Error getting MCP tools: {e}")
            raise

    async def process_query(self, query: str):
        try:
            self.logger.info(f"Processing query: {query}")
            user_message = {"role": "user", "content": query}
            self.messages = [user_message]

            while True:
                response = await self.call_llm()

                content = response["choices"][0]["message"]["content"]
                assistant_message = {
                    "role": "assistant",
                    "content": content,
                }
                self.messages.append(assistant_message)
                await self.log_conversation()
                break

            return self.messages

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise

    async def call_llm(self):
        try:
            self.logger.info("Calling local Ollama LLM")

            # Ensure base_url is set for Ollama
            if not hasattr(self, 'base_url') or not self.base_url:
                self.base_url = "http://localhost:11434/api/chat"

            headers = {
                "Content-Type": "application/json",
            }

            # Build payload for Ollama
            payload = {
                "model": "qwen3:1.7b",
                "messages": self.messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1000,  # Max tokens for Ollama
                }
            }

            # Add tools to payload if available (Ollama format)
            if self.tools:
                # Format tools for Ollama
                formatted_tools = []
                for tool in self.tools:
                    formatted_tool = {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["input_schema"]
                        }
                    }
                    formatted_tools.append(formatted_tool)

                payload["tools"] = formatted_tools

            self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for local processing
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                )

            self.logger.debug(f"Response status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text
                self.logger.error(f"Ollama Error: {response.status_code} - {error_text}")

                # Try to parse Ollama error for better debugging
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_message = error_json["error"]
                        self.logger.error(f"Ollama API Error: {error_message}")
                        raise Exception(f"Ollama Error: {error_message}")
                except json.JSONDecodeError:
                    pass  # If we can't parse the error, use the original text

                # Check for common Ollama issues
                if response.status_code == 404:
                    raise Exception(f"Model 'qwen3:1.7b' not found. Please run: ollama pull qwen3:1.7b")
                elif response.status_code == 500:
                    raise Exception(f"Ollama server error. Check if Ollama is running and the model is available.")
                else:
                    raise Exception(f"Ollama Error: {response.status_code} - {error_text}")

            try:
                response_data = response.json()
                self.logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")

                # Ollama response format validation
                if "message" in response_data:
                    # Single response format
                    if "content" not in response_data["message"]:
                        raise Exception("No content in Ollama response message")

                    # Convert to OpenAI-compatible format for consistency
                    formatted_response = {
                        "choices": [{
                            "message": {
                                "role": response_data["message"]["role"],
                                "content": response_data["message"]["content"]
                            },
                            "finish_reason": "stop"
                        }],
                        "model": response_data.get("model", "qwen3:1.7b"),
                        "usage": {
                            "prompt_tokens": response_data.get("prompt_eval_count", 0),
                            "completion_tokens": response_data.get("eval_count", 0),
                            "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count",
                                                                                                          0)
                        }
                    }

                    # Handle tool calls if present
                    if "tool_calls" in response_data["message"]:
                        formatted_response["choices"][0]["message"]["tool_calls"] = response_data["message"][
                            "tool_calls"]

                    return formatted_response

                else:
                    self.logger.error(f"Unexpected Ollama response format: {response_data}")
                    raise Exception(f"Invalid response format from Ollama: missing 'message'")

            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {str(e)}")
                self.logger.error(f"Response text was: {response.text}")
                raise Exception(f"Failed to parse JSON response from Ollama: {str(e)}")

        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout calling Ollama: {str(e)}")
            raise Exception(f"Ollama request timeout. The model might be slow to respond: {str(e)}")
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error calling Ollama: {str(e)}")
            raise Exception(f"Cannot connect to Ollama. Make sure Ollama is running on {self.base_url}: {str(e)}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error calling Ollama: {str(e)}")
            raise Exception(f"Network error connecting to Ollama: {str(e)}")
        except Exception as e:
            self.logger.error(f"Exception in call_llm: {str(e)}")
            self.logger.error(f"Exception type: {type(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            traceback.print_exc()
            raise

    async def log_conversation(self):
        os.makedirs("conversations", exist_ok=True)

        serializable_conversation = []

        for message in self.messages:
            try:
                serializable_message = {"role": message["role"], "content": []}

                if isinstance(message["content"], str):
                    serializable_message["content"] = message["content"]
                elif isinstance(message["content"], list):
                    for content_item in message["content"]:
                        if hasattr(content_item, "to_dict"):
                            serializable_message["content"].append(
                                content_item.to_dict()
                            )
                        elif hasattr(content_item, "dict"):
                            serializable_message["content"].append(content_item.dict())
                        elif hasattr(content_item, "model_dump"):
                            serializable_message["content"].append(
                                content_item.model_dump()
                            )
                        else:
                            serializable_message["content"].append(content_item)

                serializable_conversation.append(serializable_message)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                self.logger.debug(f"Message content: {message}")
                raise

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join("conversations", f"conversation_{timestamp}.json")

        try:
            with open(filepath, "w") as f:
                json.dump(serializable_conversation, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing conversation to file: {str(e)}")
            self.logger.debug(f"Serializable conversation: {serializable_conversation}")
            raise
