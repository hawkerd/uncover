import asyncio
from mcp.client.streamable_http import streamablehttp_client
import asyncio
from contextlib import AsyncExitStack
from typing import Optional, List, Dict, Any
from mcp import ClientSession
from mcp.types import CallToolResult
from openai import AsyncOpenAI
import json
import logging
import threading


class LoopRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

    def run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

class MCPOpenAIClient:
    def __init__(self):
        """Initialize the OpenAI MCP client.

        Args:
            model: The OpenAI model to use.
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model = "gpt-4o"
        self.openai_client = AsyncOpenAI()
        self.read_stream = None
        self.write_stream = None
        self.runner = LoopRunner()

    def connect_to_server(self, address: str) -> None:
        """Connect to an MCP server via streamable HTTP.

        Args:
            address: The HTTP address of the MCP server.
        """
        logging.info(f"connect_to_server: Connecting to MCP server at {address}")
        self.runner.run(self._connect_to_server(address))
        logging.info("connect_to_server: Connected to MCP server")
    async def _connect_to_server(self, address: str) -> None:
        """Connect to an MCP server via streamable HTTP.

        Args:
            address: The HTTP address of the MCP server.
        """
        # connect to the server
        self.read_stream, self.write_stream, _ = await self.exit_stack.enter_async_context(
            streamablehttp_client(address)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.read_stream, self.write_stream)
        )

        # initialize the session
        await self.session.initialize()

        # list available tools
        tools_result = await self.session.list_tools()
        logging.info("\nConnected to server with tools:")
        for tool in tools_result.tools:
            logging.info(f"  - {tool.name}: {tool.description}")

    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server in OpenAI format.

        Returns:
            A list of tools in OpenAI format.
        """
        logging.info("get_mcp_tools: Fetching available tools from MCP server")
        return self.runner.run(self._get_mcp_tools())
    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server in OpenAI format.

        Returns:
            A list of tools in OpenAI format.
        """
        tools_result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]

    def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from OpenAI.
        """
        return self.runner.run(self._process_query(query))
    async def _process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from OpenAI.
        """
        logging.info(f"process_query: Processing query: {query}")

        # get available tools
        logging.info("process_query: Fetching available tools from MCP server")
        tools = await self._get_mcp_tools()
        logging.info(f"process_query: Available tools: {tools}")

        # track messages
        messages = [{"role": "user", "content": query}]

        # initial OpenAI API call
        logging.info(f"process_query: Making initial OpenAI API call with model {self.model}")
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )
        logging.info(f"process_query: OpenAI API initial response: {response}")

        # update messages
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # handle tool calls
        while assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                logging.info(f"process_query: Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                try:
                    result: CallToolResult = await self.session.call_tool(
                        tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                    )
                    assert result.isError is False and result.content is not None
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result.content[0].text if result.content else "",
                        }
                    )
                except Exception as e:
                    logging.info(f"Error calling tool {tool_call.function.name}: {e}")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error calling tool {tool_call.function.name}: {e}",
                        }
                    )

            # Get updated response from OpenAI with tool results
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                assistant_message = response.choices[0].message
                messages.append(assistant_message)
            except Exception as e:
                logging.info(f"Error during OpenAI chat completion: {e}")
                return ""

        return assistant_message.content

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.runner.run(self._cleanup())
    async def _cleanup(self) -> None:
        await self.exit_stack.aclose()


# async def main():
#     client = MCPOpenAIClient()
#     await client.connect_to_server("http://localhost:8050/mcp")

#     query = """
#         Create a map of Minneapolis with markers for important locations, and then post the map to Instagram with the caption "Check out this map of Minneapolis!". Use your tools. You are smart
#     """

#     logging.info(f"\nQuery: {query}")

#     response = await client.process_query(query)
#     logging.info(f"\nResponse: {response}")

#     await client.cleanup()



# if __name__ == "__main__":
#     asyncio.run(main())