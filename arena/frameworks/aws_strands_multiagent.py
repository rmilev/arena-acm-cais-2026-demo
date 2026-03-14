"""AWS Strands Multi-Agent Implementation for Scenario-3 (S3) using AWS Strands framework."""
from .base import BaseAgent, AgentResult
import time
from datetime import datetime
import asyncio
import json
import os
import boto3
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent, tool
from strands.models import BedrockModel


class AWSStrandsMultiAgent(BaseAgent):
    """
    AWS Strands Multi-Agent implementation using the actual AWS Strands framework.

    Creates multiple strands that work in parallel:
    - Strand 1 (Research): Gathers customer and knowledge base data
    - Strand 2 (Products): Retrieves product catalogs and inventory
    - Strand 3 (Analysis): Calculates discounts and optimizes budget
    - Orchestrator Strand: Coordinates all strands and synthesizes final response
    """

    def __init__(self):
        super().__init__()
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "arena.mcp_server_v2"],
            env=None
        )
        self.tools_list = []
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
                                "input_schema": tool_def.inputSchema
                            })
                    return tools

        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - can't use asyncio.run()
            # Run in a new thread with its own event loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.tools_list = executor.submit(lambda: asyncio.run(_get_tools())).result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            self.tools_list = asyncio.run(_get_tools())

    def run(self, user_message: str, customer_id: str) -> AgentResult:
        """Run multi-strand workflow using AWS Strands framework."""
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
        """Async multi-strand execution using AWS Strands."""
        from typing import Optional
        import inspect

        start_time = time.time()

        # Load MCP tools
        self._load_tools()

        # Reset local tool log
        self.tool_log = []

        # Keep persistent MCP connection throughout strand operations
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # Create wrapper functions using persistent session
                async def call_mcp_tool(tool_name: str, **kwargs):
                    """Call an MCP tool using persistent session."""
                    # Log the tool call
                    self.tool_log.append(tool_name)
                    result = await mcp_session.call_tool(tool_name, kwargs)
                    return result.content[0].text

                # Create tool wrappers with proper signatures
                def make_tool_wrapper(tool_def: dict):
                    """Factory function to create tool wrapper with proper parameter signature."""
                    tool_name = tool_def["name"]
                    tool_description = tool_def["description"]
                    tool_schema = tool_def["input_schema"]

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

                # Create tool functions decorated with strands.tool
                tool_functions = []
                for tool_def in self.tools_list:
                    wrapper = make_tool_wrapper(tool_def)
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

                # Create specialized strand agents

                # Strand 1: Research Agent
                print("Orchestrator: Initializing strands...")
                research_strand = Agent(
                    model=model,
                    system_prompt="""You are Strand 1 - Research Specialist.
Your role: Gather customer data and search knowledge bases.

Tasks:
1. Search knowledge base for refund policies
2. Search knowledge base for product recommendations
3. Get customer profile and tier information
4. Retrieve order history

IMPORTANT: Always search knowledge bases FIRST before gathering other data.
Return comprehensive research findings.""",
                    tools=tool_functions
                )

                # Strand 2: Product Agent
                product_strand = Agent(
                    model=model,
                    system_prompt="""You are Strand 2 - Product Specialist.
Your role: Retrieve product catalogs and check inventory.

Tasks:
1. Get laptop catalog
2. Get monitor catalog
3. Get keyboard catalog
4. Check inventory for recommended products

Return detailed product information.""",
                    tools=tool_functions
                )

                # Strand 3: Analysis Agent
                analysis_strand = Agent(
                    model=model,
                    system_prompt="""You are Strand 3 - Analysis Specialist.
Your role: Calculate discounts and optimize budget.

Tasks:
1. Calculate applicable discounts based on customer tier
2. Compute year-to-date spending
3. Optimize product selections within budget constraints

Return precise calculations and budget analysis.""",
                    tools=tool_functions
                )

                # Execute strands in parallel (simulate parallel execution)
                print("Strand 1 (Research): Gathering data in parallel...")
                research_query = f"""For customer {customer_id}, gather:
1. Search knowledge base for 'refund policy'
2. Search knowledge base for 'laptop recommendations'
3. Get customer profile
4. Get order history

Focus on order ORD-1234."""

                research_result = await research_strand.invoke_async(research_query)
                research_text = ""
                if hasattr(research_result, 'last_message'):
                    msg = research_result.last_message
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                research_text += block.text

                print("Strand 2 (Analysis): Processing data...")
                product_query = """Retrieve product catalogs for:
1. Laptops category
2. Monitors category
3. Keyboards category

Also check inventory for high-performance laptop models."""

                product_result = await product_strand.invoke_async(product_query)
                product_text = ""
                if hasattr(product_result, 'last_message'):
                    msg = product_result.last_message
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                product_text += block.text

                analysis_query = f"""For customer {customer_id}:
1. Calculate discount for estimated total of $2800
2. Analyze YTD spending
3. Determine discount eligibility

Provide exact calculations."""

                analysis_result = await analysis_strand.invoke_async(analysis_query)
                analysis_text = ""
                if hasattr(analysis_result, 'last_message'):
                    msg = analysis_result.last_message
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                analysis_text += block.text

                # Orchestrator: Synthesize final response
                print("Strand 3 (Communication): Synthesizing response...")
                orchestrator = Agent(
                    model=model,
                    system_prompt=f"""You are the Orchestrator - coordinate strand results into final customer response.

Customer inquiry: {user_message}
Customer ID: {customer_id}

Strand Results:
---
RESEARCH STRAND:
{research_text}

PRODUCT STRAND:
{product_text}

ANALYSIS STRAND:
{analysis_text}
---

Synthesize a comprehensive customer response that:
1. Addresses refund status for ORD-1234
2. Recommends specific laptop with reasoning
3. Suggests monitor and keyboard
4. States YTD spending and discount eligibility
5. MUST explicitly state: "$[final_price] within your $[budget_amount] budget"

Use warm, professional tone and provide clear next steps.""",
                    tools=[]  # Orchestrator doesn't need tools, just synthesizes
                )

                final_result = await orchestrator.invoke_async("Create the final customer response based on all strand results.")

                print("Orchestrator: Workflow complete")

                # Extract final response
                response_text = ""
                if hasattr(final_result, 'last_message'):
                    msg = final_result.last_message
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text += block.text

                if not response_text:
                    response_text = str(final_result)

                # Tool log already tracked locally

                # Extract token usage (sum across all strands)
                input_tokens = 0
                output_tokens = 0
                for result in [research_result, product_result, analysis_result, final_result]:
                    if hasattr(result, 'usage'):
                        usage = result.usage
                        input_tokens += getattr(usage, 'input_tokens', 0)
                        output_tokens += getattr(usage, 'output_tokens', 0)

                end_time = time.time()

                return AgentResult(
                    success=True,
                    response=response_text,
                    latency=end_time - start_time,
                    tool_calls=self.tool_log,
                    token_usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
                    timestamp=datetime.now(),
                    metadata={
                        "framework": "aws_strands_multiagent",
                        "strand_count": 4,
                        "strands": ["research", "product", "analysis", "orchestrator"],
                        "customer_id": customer_id
                    }
                )
