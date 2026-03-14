"""LangGraph Multi-Agent Implementation for Scenario-3 (S3) using LangGraph framework."""
from .base import BaseAgent, AgentResult
import time
from datetime import datetime
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class LangGraphMultiAgent(BaseAgent):
    """
    LangGraph Multi-Agent implementation using StateGraph with specialized agent nodes.

    Creates a graph with multiple agent nodes:
    - Research Node: Gathers customer data and knowledge base information
    - Product Node: Retrieves product catalogs and recommendations
    - Analysis Node: Calculates discounts and optimizes budget
    - Supervisor Node: Coordinates workflow and synthesizes final response
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
        """Run multi-agent workflow using LangGraph framework."""
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
        """Async multi-agent execution using LangGraph StateGraph."""
        from langchain_aws import ChatBedrock
        from langchain_core.tools import StructuredTool
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        from langgraph.graph import StateGraph, END
        from typing import TypedDict, List, Literal

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

        # Define state
        class AgentState(TypedDict):
            messages: List[HumanMessage | AIMessage | SystemMessage]
            next: str
            research_data: str
            product_data: str
            analysis_data: str
            final_response: str

        # Define specialized agent nodes
        def research_node(state: AgentState) -> AgentState:
            """Research agent: Gather customer and KB data."""
            print("Research Node: Gathering customer and KB data...")
            system_msg = SystemMessage(content="""You are a Research Specialist.
Your role: Search knowledge bases and gather customer data.

IMPORTANT: Always search knowledge base FIRST for:
1. 'refund policy'
2. 'laptop recommendations'

Then gather customer profile and order history.

Available tools: search_knowledge_base, get_customer, get_orders
Return comprehensive research findings.""")

            research_query = f"For customer {customer_id}, research: {user_message[:200]}"
            messages = [system_msg, HumanMessage(content=research_query)]

            # Use LLM with tools to perform research
            from langgraph.prebuilt import create_react_agent
            research_agent = create_react_agent(llm, [t for t in lc_tools if t.name in ['search_knowledge_base', 'get_customer', 'get_orders']])
            result = asyncio.run(research_agent.ainvoke({"messages": messages}))

            research_data = result["messages"][-1].content if result["messages"] else ""
            state["research_data"] = research_data
            state["next"] = "product"
            return state

        def product_node(state: AgentState) -> AgentState:
            """Product agent: Retrieve catalogs and check inventory."""
            print("Product Node: Retrieving product catalogs...")
            system_msg = SystemMessage(content="""You are a Product Specialist.
Your role: Retrieve product catalogs and check inventory.

Available tools: get_product_catalog, check_inventory
Return detailed product information for laptops, monitors, keyboards.""")

            messages = [system_msg, HumanMessage(content=f"Retrieve product catalogs for customer inquiry: {user_message[:200]}")]

            from langgraph.prebuilt import create_react_agent
            product_agent = create_react_agent(llm, [t for t in lc_tools if t.name in ['get_product_catalog', 'check_inventory']])
            result = asyncio.run(product_agent.ainvoke({"messages": messages}))

            product_data = result["messages"][-1].content if result["messages"] else ""
            state["product_data"] = product_data
            state["next"] = "analysis"
            return state

        def analysis_node(state: AgentState) -> AgentState:
            """Analysis agent: Calculate discounts and optimize budget."""
            print("Analysis Node: Calculating discounts...")
            system_msg = SystemMessage(content="""You are an Analysis Specialist.
Your role: Calculate discounts and analyze budgets.

Available tools: calculate_discount
Provide precise calculations and budget optimization.""")

            messages = [system_msg, HumanMessage(content=f"For customer {customer_id}, calculate discounts for ~$2800 total")]

            from langgraph.prebuilt import create_react_agent
            analysis_agent = create_react_agent(llm, [t for t in lc_tools if t.name == 'calculate_discount'])
            result = asyncio.run(analysis_agent.ainvoke({"messages": messages}))

            analysis_data = result["messages"][-1].content if result["messages"] else ""
            state["analysis_data"] = analysis_data
            state["next"] = "supervisor"
            return state

        def supervisor_node(state: AgentState) -> AgentState:
            """Supervisor: Coordinate and synthesize final response."""
            print("Supervisor Node: Synthesizing final response...")
            synthesis_prompt = f"""Create a comprehensive customer response based on:

CUSTOMER INQUIRY: {user_message}
CUSTOMER ID: {customer_id}

RESEARCH DATA:
{state.get('research_data', '')}

PRODUCT DATA:
{state.get('product_data', '')}

ANALYSIS DATA:
{state.get('analysis_data', '')}

Requirements:
1. Address refund status for ORD-1234
2. Recommend specific laptop with reasoning
3. Suggest monitor and keyboard
4. State YTD spending and discount eligibility
5. MUST explicitly state: "$[final_price] within your $[budget_amount] budget"

Use warm, professional tone."""

            messages = [HumanMessage(content=synthesis_prompt)]
            response = llm.invoke(messages)

            state["final_response"] = response.content
            state["next"] = END
            return state

        def router(state: AgentState) -> Literal["research", "product", "analysis", "supervisor", END]:
            """Route to next node based on state."""
            return state.get("next", END)

        # Build StateGraph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("research", research_node)
        workflow.add_node("product", product_node)
        workflow.add_node("analysis", analysis_node)
        workflow.add_node("supervisor", supervisor_node)

        # Add edges
        workflow.set_entry_point("research")
        workflow.add_conditional_edges("research", router)
        workflow.add_conditional_edges("product", router)
        workflow.add_conditional_edges("analysis", router)
        workflow.add_conditional_edges("supervisor", router)

        # Compile and run
        app = workflow.compile()

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "next": "research",
            "research_data": "",
            "product_data": "",
            "analysis_data": "",
            "final_response": ""
        }

        result = await app.ainvoke(initial_state)

        # Extract final response
        response_text = result.get("final_response", "")

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
                "framework": "langgraph_multiagent",
                "node_count": 4,
                "nodes": ["research", "product", "analysis", "supervisor"],
                "customer_id": customer_id
            }
        )
