"""Google ADK Multi-Agent Implementation for Scenario-3 (S3) using Google ADK framework."""
from .base import BaseAgent, AgentResult
import time
from datetime import datetime
import asyncio
import json
import os
import litellm
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GoogleADKMultiAgent(BaseAgent):
    """
    Google ADK Multi-Agent implementation using the actual Google ADK framework.

    Creates specialized agents:
    - Research Agent: Gathers customer data and knowledge base information
    - Product Agent: Handles product catalogs and recommendations
    - Analysis Agent: Calculates discounts and optimizes budget
    - Coordinator Agent: Orchestrates workflow and synthesizes final response
    """

    def __init__(self):
        super().__init__()
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "arena.mcp_server_v2"],
            env=None
        )
        self.tools = []
        self.tool_log = []

    def _load_tools(self):
        """Load MCP tools synchronously."""
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

        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - can't use asyncio.run()
            # Run in a new thread with its own event loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.tools = executor.submit(lambda: asyncio.run(_get_tools())).result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            self.tools = asyncio.run(_get_tools())

    def run(self, user_message: str, customer_id: str) -> AgentResult:
        """Run multi-agent workflow using Google ADK framework."""
        start_time = time.time()

        try:
            result = asyncio.run(self._run_async(user_message, customer_id))
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()

            return AgentResult(
                success=False,
                response=f"Error: {str(e)}",
                latency=time.time() - start_time,
                tool_calls=[],
                token_usage={"input_tokens": 0, "output_tokens": 0},
                timestamp=datetime.now(),
                metadata={"error": str(e), "customer_id": customer_id}
            )

    async def _run_async(self, user_message: str, customer_id: str) -> AgentResult:
        """Async multi-agent execution using Google ADK."""
        from google.adk.agents import LlmAgent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.adk.models.lite_llm import LiteLlm
        from google.genai import types
        import inspect
        from typing import Optional

        start_time = time.time()

        # Hard-inject the model into LiteLLM's cost dictionary
        litellm.model_cost["bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"] = {
            "max_tokens": 64000,
            "max_input_tokens": 200000,
            "max_output_tokens": 64000,
            "litellm_provider": "bedrock",
            "mode": "chat"
        }

        # Load MCP tools
        self._load_tools()

        # Reset local tool log
        self.tool_log = []

        # Keep persistent MCP connection throughout agent runs
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # Create tool calling function with persistent session
                async def call_mcp_tool(tool_name: str, **kwargs):
                    """Call MCP tool using persistent session."""
                    # Log the tool call
                    self.tool_log.append(tool_name)
                    result = await mcp_session.call_tool(tool_name, kwargs)
                    return result.content[0].text

                # Convert MCP tools to Google ADK tool functions
                def make_tool_wrapper(tool_def: dict):
                    """Factory to create tool function with proper parameter signature."""
                    tool_name = tool_def["name"]
                    tool_description = tool_def["description"]
                    tool_params = tool_def["parameters"]

                    required_params = tool_params.get("required", [])
                    properties = tool_params.get("properties", {})

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

                # Set AWS environment
                os.environ["AWS_REGION_NAME"] = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

                # Initialize Session Service
                app_name = "MultiAgentCustomerSupport"
                user_id = f"user-{customer_id}"
                session_id = "session-multiagent-001"

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

                # Create specialized agents using Google ADK

                # Research Agent - handles customer and knowledge base data
                research_agent = LlmAgent(
                    name="ResearchAgent",
                    description="Research specialist that gathers customer data and searches knowledge bases",
                    instruction="""You are a research specialist. Your role is to:
1. Search knowledge bases for relevant policies (refunds, product recommendations)
2. Gather customer profile and tier information
3. Retrieve order history and status
4. Compile comprehensive research data for analysis

IMPORTANT: Always search knowledge base FIRST before gathering other data.""",
                    model=claude_model,
                    tools=adk_tools
                )

                # Product Agent - handles product catalogs and recommendations
                product_agent = LlmAgent(
                    name="ProductAgent",
                    description="Product specialist that retrieves catalogs and makes recommendations",
                    instruction="""You are a product specialist. Your role is to:
1. Retrieve product catalogs (laptops, monitors, keyboards)
2. Match products to customer needs
3. Consider customer purchase history
4. Recommend compatible products

Focus on quality and compatibility.""",
                    model=claude_model,
                    tools=adk_tools
                )

                # Analysis Agent - handles calculations and budget optimization
                analysis_agent = LlmAgent(
                    name="AnalysisAgent",
                    description="Analysis specialist that calculates discounts and optimizes budgets",
                    instruction="""You are an analysis specialist. Your role is to:
1. Calculate applicable discounts based on customer tier
2. Compute year-to-date spending
3. Optimize product selections within budget constraints
4. Provide accurate pricing breakdowns

Be precise with numbers and ensure budget compliance.""",
                    model=claude_model,
                    tools=adk_tools
                )

                # Coordinator Agent - orchestrates workflow and synthesizes response
                coordinator_agent = LlmAgent(
                    name="CoordinatorAgent",
                    description="Main coordinator that orchestrates multi-agent workflow and creates final response",
                    instruction=f"""You are the main coordinator managing a team of specialist agents.

Your team:
- ResearchAgent: Gathers customer data and knowledge base information
- ProductAgent: Retrieves product catalogs and makes recommendations
- AnalysisAgent: Calculates discounts and optimizes budgets

Customer inquiry:
{user_message}

Customer ID: {customer_id}

Your workflow:
1. Direct ResearchAgent to search knowledge bases and gather customer data
2. Direct ProductAgent to retrieve relevant product catalogs
3. Direct AnalysisAgent to calculate discounts and optimize budget
4. Synthesize all information into a comprehensive customer response

Requirements for final response:
- Address all customer questions clearly
- Include specific product recommendations with names and IDs
- MUST explicitly state: "$[final_price] within your $[budget_amount] budget"
- Provide clear next steps
- Use warm, professional tone""",
                    model=claude_model,
                    tools=adk_tools
                )

                # Create Runner for coordinator (main orchestrator)
                runner = Runner(
                    agent=coordinator_agent,
                    app_name=app_name,
                    session_service=session_service
                )

                # Create message content
                message_content = types.Content(
                    role='user',
                    parts=[types.Part.from_text(text=f"Please help customer {customer_id} with their inquiry: {user_message}")]
                )

                # Run the coordinator agent
                response_text = ""
                async for event in runner.run_async(
                    session_id=session.id,
                    user_id=user_id,
                    new_message=message_content
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            response_text = event.content.parts[0].text

                # Tool log already tracked locally
                end_time = time.time()

                return AgentResult(
                    success=True,
                    response=response_text,
                    latency=end_time - start_time,
                    tool_calls=self.tool_log,
                    token_usage={"input_tokens": 0, "output_tokens": 0},  # TODO: track tokens
                    timestamp=datetime.now(),
                    metadata={
                        "framework": "google_adk_multiagent",
                        "agent_count": 4,
                        "agents": ["research", "product", "analysis", "coordinator"],
                        "customer_id": customer_id
                    }
                )
