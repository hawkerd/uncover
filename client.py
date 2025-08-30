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
        self.read_stream = None
        self.write_stream = None

    async def connect_to_server(self, address: str) -> None:
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
        print("\nConnected to server with tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
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

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from OpenAI.
        """
        # get aavailable tools
        tools = await self.get_mcp_tools()

        # Initial OpenAI API call
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )
        print(f"OpenAI API initial response: {response}")

        # Get assistant's response
        assistant_message = response.choices[0].message

        # Initialize conversation with user query and assistant response
        messages = [
            {"role": "user", "content": query},
            assistant_message,
        ]

        # handle tool calls
        while assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                print(f"Calling tool: {tool_call.function.name} with arguments: {tool_call.function.arguments}")
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
                    print(f"Error calling tool {tool_call.function.name}: {e}")
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
                print(f"Error during OpenAI chat completion: {e}")
                return ""

        return assistant_message.content

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPOpenAIClient()
    await client.connect_to_server("http://localhost:8050/mcp")

    query = """
        Create a map of Minneapolis with markers for important locations, and then post the map to Instagram with the caption "Check out this map of Minneapolis!". Use your tools. You are smart
    """

    print(f"\nQuery: {query}")

    response = await client.process_query(query)
    print(f"\nResponse: {response}")

    await client.cleanup()



if __name__ == "__main__":
    asyncio.run(main())