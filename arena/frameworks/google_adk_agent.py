"""Google ADK framework adapter with Bedrock Claude via LiteLLM."""
import os
import sys
import asyncio
import json
import litellm
from arena.frameworks.base import FrameworkAdapter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GoogleADKAdapter(FrameworkAdapter):
    """Google ADK with Bedrock Claude and MCP tools.

    Uses Google's ADK LlmAgent + Runner framework powered by Claude on AWS Bedrock via LiteLLM.
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
            args=["arena/mcp_server.py"],
            env=None
        )

    def connect_to_mcp(self):
        """Connect and load MCP tools."""
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
        """Run Google ADK agent."""
        return asyncio.run(self._run_agent_async(user_message))

    async def _run_agent_async(self, user_message: str) -> str:
        """Async agent execution using Google ADK."""
        from google.adk.agents import LlmAgent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.adk.models.lite_llm import LiteLlm
        from google.genai import types

        # Hard-inject the model into LiteLLM's cost dictionary to bypass validation
        litellm.model_cost["bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"] = {
            "max_tokens": 64000,
            "max_input_tokens": 200000,
            "max_output_tokens": 64000,
            "litellm_provider": "bedrock",
            "mode": "chat"
        }

        # Keep persistent MCP connection throughout agent run
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # Reset MCP log
                await mcp_session.call_tool("arena_reset_log", {})

                # Create tool calling function with persistent session
                async def call_mcp_tool(tool_name: str, **kwargs):
                    """Call MCP tool using persistent session."""
                    result = await mcp_session.call_tool(tool_name, kwargs)
                    return result.content[0].text

                # Convert MCP tools to Google ADK tool functions with proper signatures
                def make_tool_wrapper(tool_def: dict):
                    """Factory to create tool function with proper parameter signature."""
                    tool_name = tool_def["name"]
                    tool_description = tool_def["description"]
                    tool_params = tool_def["parameters"]

                    # Build function with dynamic parameters based on schema
                    # Get required parameters from schema
                    required_params = tool_params.get("required", [])
                    properties = tool_params.get("properties", {})

                    # Create parameter signature dynamically
                    import inspect
                    from typing import Optional

                    # Build parameters list
                    params = []
                    for param_name, param_spec in properties.items():
                        if param_name in required_params:
                            params.append(inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                annotation=str  # Simplify to str for now
                            ))
                        else:
                            params.append(inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                default=None,
                                annotation=Optional[str]
                            ))

                    # Create async function with proper signature
                    async def tool_func(**kwargs) -> str:
                        """Tool wrapper that calls MCP."""
                        return await call_mcp_tool(tool_name, **kwargs)

                    # Set signature
                    tool_func.__signature__ = inspect.Signature(params)
                    tool_func.__name__ = tool_name
                    tool_func.__doc__ = tool_description

                    return tool_func

                adk_tools = []
                for tool_def in self.tools:
                    tool_wrapper = make_tool_wrapper(tool_def)
                    adk_tools.append(tool_wrapper)

                try:
                    # Set AWS environment
                    os.environ["AWS_REGION_NAME"] = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

                    # Initialize Session Service
                    app_name = "CustomerSupportApp"
                    user_id = "user-001"
                    session_id = "session-001"

                    session_service = InMemorySessionService()
                    session = await session_service.create_session(
                        app_name=app_name,
                        user_id=user_id,
                        session_id=session_id
                    )

                    # Wrap the model string in LiteLlm object
                    claude_model = LiteLlm(
                        model="bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
                    )

                    # Create Google ADK LlmAgent with Bedrock Claude via LiteLLM
                    agent = LlmAgent(
                        name="CustomerSupportAgent",
                        description="A customer support agent that helps with orders, refunds, and inquiries.",
                        instruction=self.system_prompt,
                        model=claude_model,
                        tools=adk_tools
                    )

                    # Create Runner
                    runner = Runner(
                        agent=agent,
                        app_name=app_name,
                        session_service=session_service
                    )

                    # Create message content
                    message_content = types.Content(
                        role='user',
                        parts=[types.Part.from_text(text=user_message)]
                    )

                    # Run the agent and collect response + token usage
                    response_text = ""
                    self._total_input_tokens = 0
                    self._total_output_tokens = 0
                    async for event in runner.run_async(
                        session_id=session.id,
                        user_id=user_id,
                        new_message=message_content
                    ):
                        # Accumulate token usage from all events
                        if hasattr(event, 'usage_metadata') and event.usage_metadata:
                            self._total_input_tokens += event.usage_metadata.prompt_token_count or 0
                            self._total_output_tokens += event.usage_metadata.candidates_token_count or 0
                        if event.is_final_response():
                            if event.content and event.content.parts:
                                response_text = event.content.parts[0].text

                    # Get tool log from the persistent session
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
        """Return tool log."""
        return self.tool_log
