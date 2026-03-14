"""AWS Strands framework adapter - simplified with direct MCP integration."""
import os
import sys
import asyncio
import json
import boto3
from arena.frameworks.base import FrameworkAdapter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent, tool
from strands.models import BedrockModel


class AWSStrandsAdapter(FrameworkAdapter):
    """AWS Strands with Bedrock and MCP tools."""

    def __init__(self, system_prompt: str):
        super().__init__(system_prompt)
        self.server_params = None
        self.tool_log = []
        self.tools_list = []

    def start_mcp_server(self):
        """MCP server will be started on demand."""
        pass

    def connect_to_mcp(self):
        """Set up MCP connection."""
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "arena.mcp_server_v2"],
            env=None
        )

        # Load tool definitions from MCP
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
                                "input_schema": tool_def.inputSchema
                            })
                    return tools

        self.tools_list = asyncio.run(_get_tools())

    def run_agent(self, user_message: str) -> str:
        """Run Strands agent."""
        return asyncio.run(self._run_agent_async(user_message))

    async def _run_agent_async(self, user_message: str) -> str:
        """Async agent execution."""
        # Keep persistent MCP connection
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # Reset tool log
                await mcp_session.call_tool("arena_reset_log", {})

                # Create wrapper functions using persistent session
                async def call_mcp_tool(tool_name: str, **kwargs):
                    """Call an MCP tool using persistent session."""
                    result = await mcp_session.call_tool(tool_name, kwargs)
                    return result.content[0].text

                # Create tool wrappers with proper signatures
                def make_tool_wrapper(tool_def: dict):
                    """Factory function to create tool wrapper with proper parameter signature."""
                    tool_name = tool_def["name"]
                    tool_description = tool_def["description"]
                    tool_schema = tool_def["input_schema"]

                    # Build function with dynamic parameters based on schema
                    import inspect
                    from typing import Optional

                    required_params = tool_schema.get("required", [])
                    properties = tool_schema.get("properties", {})

                    # Build parameters list
                    params = []
                    for param_name, param_spec in properties.items():
                        if param_name in required_params:
                            params.append(inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                annotation=str
                            ))
                        else:
                            params.append(inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                default=None,
                                annotation=Optional[str]
                            ))

                    async def tool_wrapper(**kwargs):
                        return await call_mcp_tool(tool_name, **kwargs)

                    # Set signature and metadata
                    tool_wrapper.__signature__ = inspect.Signature(params)
                    tool_wrapper.__name__ = tool_name
                    tool_wrapper.__doc__ = tool_description

                    return tool_wrapper

                tool_functions = []
                for tool_def in self.tools_list:
                    # Create wrapper with proper signature
                    wrapper = make_tool_wrapper(tool_def)

                    # Wrap with strands.tool decorator
                    decorated_tool = tool(
                        name=tool_def["name"],
                        description=tool_def["description"]
                    )(wrapper)

                    tool_functions.append(decorated_tool)

                # Create Bedrock model
                boto_session = boto3.Session(
                    profile_name=os.getenv("AWS_PROFILE", "prod-tools"),
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                )

                model = BedrockModel(
                    boto_session=boto_session,
                    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                    temperature=0
                )

                # Create agent with MCP tools
                agent = Agent(
                    model=model,
                    system_prompt=self.system_prompt,
                    tools=tool_functions
                )

                # Run agent
                try:
                    result = await agent.invoke_async(user_message)

                    # Extract response
                    response_text = ""
                    if hasattr(result, 'last_message'):
                        msg = result.last_message
                        if hasattr(msg, 'content'):
                            for block in msg.content:
                                if hasattr(block, 'text'):
                                    response_text += block.text

                    if not response_text:
                        response_text = str(result)

                    # Extract token usage from AgentResult.metrics.accumulated_usage
                    self._total_input_tokens = 0
                    self._total_output_tokens = 0
                    if hasattr(result, 'metrics') and result.metrics:
                        usage = result.metrics.accumulated_usage
                        self._total_input_tokens = usage.get("inputTokens", 0)
                        self._total_output_tokens = usage.get("outputTokens", 0)

                    # Get tool log from persistent MCP session
                    log_result = await mcp_session.call_tool("arena_get_log", {})
                    self.tool_log = json.loads(log_result.content[0].text)

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
