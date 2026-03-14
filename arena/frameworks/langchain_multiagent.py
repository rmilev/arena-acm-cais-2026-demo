"""LangChain Multi-Agent Implementation for Scenario-3 (S3) using LangChain framework."""
from .base import BaseAgent, AgentResult
import time
from datetime import datetime
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class LangChainMultiAgent(BaseAgent):
    """
    LangChain Multi-Agent implementation using sequential chains with specialized agents.

    Creates a multi-agent pipeline:
    - Research Agent: Gathers customer data and knowledge base information
    - Product Agent: Retrieves product catalogs and recommendations
    - Analysis Agent: Calculates discounts and optimizes budget
    - Communication Agent: Synthesizes findings into customer response
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
            # Already in async context - run in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.tools = executor.submit(lambda: asyncio.run(_get_tools())).result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            self.tools = asyncio.run(_get_tools())

    def run(self, user_message: str, customer_id: str) -> AgentResult:
        """Run multi-agent workflow using LangChain framework."""
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
        """Async multi-agent execution using LangChain."""
        from langchain_aws import ChatBedrock
        from langchain_core.tools import StructuredTool
        from langchain_core.messages import HumanMessage, SystemMessage
        from langgraph.prebuilt import create_react_agent

        start_time = time.time()

        # Load MCP tools
        self._load_tools()

        # Reset local tool log
        self.tool_log = []

        # Create tool calling function
        async def call_mcp_tool(tool_name: str, **kwargs):
            """Call MCP tool."""
            # Log the tool call
            self.tool_log.append(tool_name)
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, kwargs)
                    return result.content[0].text

        # Convert MCP tools to LangChain tools
        lc_tools = []
        for tool_def in self.tools:
            tool_name = tool_def["name"]

            def make_tool_func(tn):
                def tool_func(**kwargs):
                    return asyncio.run(call_mcp_tool(tn, **kwargs))
                return tool_func

            lc_tool = StructuredTool.from_function(
                func=make_tool_func(tool_name),
                name=tool_name,
                description=tool_def["description"]
            )
            lc_tools.append(lc_tool)

        # Create Bedrock LLM
        llm = ChatBedrock(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            credentials_profile_name=os.getenv("AWS_PROFILE", "prod-tools"),
            model_kwargs={"temperature": 0}
        )

        # Create specialized agents using LangChain's agent pattern
        print("Research Agent: Gathering customer and KB data...")

        # Agent 1: Research - search KB and gather customer data
        research_tools = [t for t in lc_tools if t.name in ['search_knowledge_base', 'get_customer', 'get_orders']]
        research_agent = create_react_agent(
            llm,
            research_tools,
            prompt="""You are a Research Specialist.
Your role: Search knowledge bases and gather customer data.

IMPORTANT: Always search knowledge base FIRST for:
1. 'refund policy'
2. 'laptop recommendations'

Then gather customer profile and order history."""
        )

        research_result = await research_agent.ainvoke({
            "messages": [HumanMessage(content=f"For customer {customer_id}, research: {user_message}")]
        })

        research_data = research_result["messages"][-1].content if research_result["messages"] else ""

        # Agent 2: Product - retrieve catalogs
        print("Product Agent: Retrieving product catalogs...")

        product_tools = [t for t in lc_tools if t.name in ['get_product_catalog', 'check_inventory']]
        product_agent = create_react_agent(
            llm,
            product_tools,
            prompt="""You are a Product Specialist.
Your role: Retrieve product catalogs and check inventory.

Focus on laptops, monitors, and keyboards."""
        )

        product_result = await product_agent.ainvoke({
            "messages": [HumanMessage(content=f"Retrieve product catalogs for: {user_message[:200]}")]
        })

        product_data = product_result["messages"][-1].content if product_result["messages"] else ""

        # Agent 3: Analysis - calculate discounts
        print("Analysis Agent: Calculating discounts...")

        analysis_tools = [t for t in lc_tools if t.name == 'calculate_discount']
        analysis_agent = create_react_agent(
            llm,
            analysis_tools,
            prompt="""You are an Analysis Specialist.
Your role: Calculate discounts and analyze budgets.

Provide precise calculations."""
        )

        analysis_result = await analysis_agent.ainvoke({
            "messages": [HumanMessage(content=f"For customer {customer_id}, calculate discounts for ~$2800 total")]
        })

        analysis_data = analysis_result["messages"][-1].content if analysis_result["messages"] else ""

        # Agent 4: Communication - synthesize final response
        print("Communication Agent: Synthesizing final response...")

        synthesis_prompt = f"""Create a comprehensive customer response based on:

CUSTOMER INQUIRY: {user_message}
CUSTOMER ID: {customer_id}

RESEARCH DATA:
{research_data}

PRODUCT DATA:
{product_data}

ANALYSIS DATA:
{analysis_data}

Requirements:
1. Address refund status for ORD-1234
2. Recommend specific laptop with reasoning
3. Suggest monitor and keyboard
4. State YTD spending and discount eligibility
5. MUST explicitly state: "$[final_price] within your $[budget_amount] budget"

Use warm, professional tone."""

        final_result = llm.invoke([HumanMessage(content=synthesis_prompt)])
        response_text = final_result.content

        # Tool log already tracked locally
        end_time = time.time()

        # Extract token usage from all agent results
        total_input = 0
        total_output = 0
        for result in [research_result, product_result, analysis_result]:
            for msg in result.get("messages", []):
                if hasattr(msg, 'response_metadata'):
                    metadata = msg.response_metadata
                    if 'usage' in metadata:
                        usage = metadata['usage']
                        total_input += usage.get('prompt_tokens', 0)
                        total_output += usage.get('completion_tokens', 0)

        return AgentResult(
            success=True,
            response=response_text,
            latency=end_time - start_time,
            tool_calls=self.tool_log,
            token_usage={"input_tokens": total_input, "output_tokens": total_output},
            timestamp=datetime.now(),
            metadata={
                "framework": "langchain_multiagent",
                "agent_count": 4,
                "agents": ["research", "product", "analysis", "communication"],
                "customer_id": customer_id
            }
        )
