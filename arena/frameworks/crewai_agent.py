"""CrewAI framework adapter with Bedrock."""
import os
import sys
import asyncio
import json
from arena.frameworks.base import FrameworkAdapter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CrewAIAdapter(FrameworkAdapter):
    """CrewAI with Bedrock and MCP tools."""

    def __init__(self, system_prompt: str):
        super().__init__(system_prompt)
        self.server_params = None
        self.tools = []
        self.tool_log = []
        self._local_tool_log = []  # Track tool calls locally

    def start_mcp_server(self):
        """MCP server setup."""
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "arena.mcp_server_v2"],
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
        """Run CrewAI agent."""
        return asyncio.run(self._run_agent_async(user_message))

    async def _run_agent_async(self, user_message: str) -> str:
        """Async agent execution."""
        from crewai import Agent, Task, Crew, LLM
        from crewai.tools import BaseTool

        # Reset local tool log
        self._local_tool_log = []

        # Create tool calling function with fresh MCP connection per call
        def call_mcp_tool_sync(tool_name: str, **kwargs):
            """Sync wrapper for MCP tool calls (required by CrewAI BaseTool).

            Uses Fix 3 with ThreadPoolExecutor: Run async code in a separate thread
            to completely avoid event loop conflicts.
            """
            import concurrent.futures

            # Log the tool call locally
            self._local_tool_log.append({
                "tool": tool_name,
                "args": kwargs
            })

            def run_in_thread():
                """Run async call in a new thread with its own event loop."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async def _async_call():
                        # Create fresh MCP connection for this tool call
                        async with stdio_client(self.server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                result = await session.call_tool(tool_name, kwargs)
                                return result.content[0].text

                    return loop.run_until_complete(_async_call())
                finally:
                    loop.close()

            # Execute in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)

        # Convert MCP tools to CrewAI tools with proper signatures
        def make_tool_class(tool_def: dict):
            """Factory to create tool class with proper parameter signature."""
            tool_name = tool_def["name"]
            tool_description = tool_def["description"]
            tool_schema = tool_def["parameters"]

            # Build Pydantic model for CrewAI BaseTool args_schema
            from pydantic import BaseModel, Field, create_model
            from typing import Optional

            required_params = tool_schema.get("required", [])
            properties = tool_schema.get("properties", {})

            # Build field definitions for Pydantic model
            fields = {}
            for param_name, param_spec in properties.items():
                param_desc = param_spec.get("description", "")
                if param_name in required_params:
                    fields[param_name] = (str, Field(..., description=param_desc))
                else:
                    fields[param_name] = (Optional[str], Field(None, description=param_desc))

            # Create dynamic Pydantic model
            ArgsModel = create_model(f'{tool_name}_args', **fields)

            class MCPTool(BaseTool):
                name: str = tool_name
                description: str = tool_description
                args_schema: type[BaseModel] = ArgsModel

                def _run(self, **kwargs):
                    return call_mcp_tool_sync(tool_name, **kwargs)

            return MCPTool()

        crewai_tools = []
        for tool_def in self.tools:
            crewai_tools.append(make_tool_class(tool_def))

        # Create Bedrock LLM using CrewAI's LLM wrapper (uses LiteLLM)
        llm = LLM(
            model=f"bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            temperature=0,
            aws_region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_profile_name=os.getenv("AWS_PROFILE", "prod-tools")
        )

        # Create agent
        agent = Agent(
            role="Customer Support Agent",
            goal="Help customers with their inquiries",
            backstory=self.system_prompt,
            tools=crewai_tools,
            verbose=True,  # Enable verbose to see tool calls
            llm=llm
        )

        # Create task
        task = Task(
            description=user_message,
            expected_output="A helpful response to the customer",
            agent=agent
        )

        # Create crew and run
        crew = Crew(agents=[agent], tasks=[task], verbose=False)

        try:
            result = crew.kickoff()

            # Extract response
            response_text = str(result)

            # Convert local tool log to evaluator format (list of tool names)
            self.tool_log = [entry["tool"] for entry in self._local_tool_log]

            # Extract token usage from crew usage_metrics
            self._total_input_tokens = 0
            self._total_output_tokens = 0
            if hasattr(crew, "usage_metrics"):
                metrics = crew.usage_metrics
                self._total_input_tokens = getattr(metrics, "prompt_tokens", 0)
                self._total_output_tokens = getattr(metrics, "completion_tokens", 0)

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
