"""LangGraph framework adapter with persistent MCP connection."""
import os
import sys
import asyncio
import json
from arena.frameworks.base import FrameworkAdapter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class LangGraphAdapter(FrameworkAdapter):
    """LangGraph with Bedrock Claude and MCP tools.

    Uses a persistent MCP session for the entire agent run so that
    tool call state (logging) is preserved across calls.
    """

    def __init__(self, system_prompt: str):
        super().__init__(system_prompt)
        self.server_params = None
        self.tools = []
        self.tool_log = []

    def start_mcp_server(self):
        """MCP server setup."""
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "arena.mcp_server_v2"],
            env=None
        )

    def connect_to_mcp(self):
        """Connect and load MCP tool definitions."""
        async def _get_tools():
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()

                    tools = []
                    for tool_def in tools_result.tools:
                        if not tool_def.name.startswith("arena_"):
                            tools.append({
                                "name": tool_def.name,
                                "description": tool_def.description,
                                "parameters": tool_def.inputSchema
                            })
                    return tools

        self.tools = asyncio.run(_get_tools())

    def run_agent(self, user_message: str) -> str:
        """Run LangGraph agent."""
        return asyncio.run(self._run_agent_async(user_message))

    async def _run_agent_async(self, user_message: str) -> str:
        """Async agent execution with persistent MCP session."""
        from langchain_aws import ChatBedrock
        from langchain_core.tools import StructuredTool
        from langchain_core.messages import HumanMessage, SystemMessage
        from langgraph.prebuilt import create_react_agent

        # Keep persistent MCP connection for the entire agent run
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # Reset tool log on the persistent session
                await mcp_session.call_tool("arena_reset_log", {})

                # Async tool caller using the persistent session
                async def call_mcp_tool(tool_name: str, **kwargs):
                    result = await mcp_session.call_tool(tool_name, kwargs)
                    return result.content[0].text

                # Convert MCP tools to LangChain StructuredTools with proper schemas
                from pydantic import BaseModel, Field, create_model
                from typing import Optional

                lc_tools = []
                for tool_def in self.tools:
                    tool_name = tool_def["name"]
                    tool_schema = tool_def.get("parameters", {})
                    required_params = tool_schema.get("required", [])
                    properties = tool_schema.get("properties", {})

                    # Build Pydantic model from MCP inputSchema
                    fields = {}
                    for param_name, param_spec in properties.items():
                        param_desc = param_spec.get("description", "")
                        if param_name in required_params:
                            fields[param_name] = (str, Field(..., description=param_desc))
                        else:
                            fields[param_name] = (Optional[str], Field(None, description=param_desc))

                    ArgsModel = create_model(f'{tool_name}_args', **fields)

                    def make_async_func(tn):
                        async def tool_func(**kwargs) -> str:
                            return await call_mcp_tool(tn, **kwargs)
                        tool_func.__name__ = tn
                        return tool_func

                    lc_tool = StructuredTool.from_function(
                        coroutine=make_async_func(tool_name),
                        name=tool_name,
                        description=tool_def["description"],
                        args_schema=ArgsModel,
                    )
                    lc_tools.append(lc_tool)

                # Create Bedrock LLM
                llm = ChatBedrock(
                    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    credentials_profile_name=os.getenv("AWS_PROFILE", "prod-tools"),
                    model_kwargs={"temperature": 0}
                )

                # Create LangGraph ReAct agent
                graph = create_react_agent(
                    llm,
                    lc_tools,
                    prompt=self.system_prompt
                )

                # Run agent
                try:
                    result = await graph.ainvoke(
                        {"messages": [HumanMessage(content=user_message)]}
                    )

                    # Extract response from messages
                    response_text = ""
                    messages = result.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            response_text = last_message.content
                        else:
                            response_text = str(last_message)

                    # Get tool log from the persistent MCP session
                    log_result = await mcp_session.call_tool("arena_get_log", {})
                    self.tool_log = json.loads(log_result.content[0].text)

                    # Extract token usage from all AI messages
                    total_input = 0
                    total_output = 0
                    for msg in messages:
                        if hasattr(msg, 'response_metadata'):
                            metadata = msg.response_metadata
                            if 'usage' in metadata:
                                usage = metadata['usage']
                                total_input += usage.get('prompt_tokens', 0)
                                total_output += usage.get('completion_tokens', 0)

                    self._total_input_tokens = total_input
                    self._total_output_tokens = total_output

                    return response_text

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return f"[Error: {str(e)}]"

    def get_token_usage(self) -> dict:
        """Return token usage."""
        return {
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
        }

    def get_tool_log(self) -> list:
        """Return tool call log."""
        return self.tool_log
