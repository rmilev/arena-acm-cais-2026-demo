"""CrewAI Multi-Agent Implementation for Scenario-3 (S3) using CrewAI framework."""
from .base import BaseAgent, AgentResult
import time
from datetime import datetime
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CrewAIMultiAgent(BaseAgent):
    """
    CrewAI Multi-Agent implementation using the actual CrewAI framework.

    Creates specialized agents:
    - Research Agent: Gathers customer data, orders, and product information
    - Analysis Agent: Evaluates options, calculates discounts, and optimizes budget
    - Communication Agent: Synthesizes findings into customer-friendly response
    """

    def __init__(self):
        super().__init__()
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "arena.mcp_server_v2"],
            env=None
        )
        self.tools = []
        self._local_tool_log = []

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

        self.tools = asyncio.run(_get_tools())

    def _make_crewai_tools(self):
        """Convert MCP tools to CrewAI tools."""
        from crewai.tools import BaseTool
        from pydantic import BaseModel, Field, create_model
        from typing import Optional
        import concurrent.futures

        def call_mcp_tool_sync(tool_name: str, **kwargs):
            """Sync wrapper for MCP tool calls (required by CrewAI BaseTool)."""
            # Log the tool call locally
            self._local_tool_log.append(tool_name)

            def run_in_thread():
                """Run async call in a new thread with its own event loop."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async def _async_call():
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

        def make_tool_class(tool_def: dict):
            """Factory to create tool class with proper parameter signature."""
            tool_name = tool_def["name"]
            tool_description = tool_def["description"]
            tool_schema = tool_def["parameters"]

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

        return crewai_tools

    def run(self, user_message: str, customer_id: str) -> AgentResult:
        """Run multi-agent workflow using CrewAI framework."""
        start_time = time.time()

        try:
            from crewai import Agent, Task, Crew, LLM
            import os

            # Reset tool log
            self._local_tool_log = []

            # Load MCP tools
            self._load_tools()
            crewai_tools = self._make_crewai_tools()

            # Create Bedrock LLM using CrewAI's LLM wrapper (uses LiteLLM)
            llm = LLM(
                model="bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                temperature=0,
                aws_region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                aws_profile_name=os.getenv("AWS_PROFILE", "prod-tools")
            )

            # Create specialized agents
            research_agent = Agent(
                role="Research Specialist",
                goal="Gather comprehensive customer data, order history, and product information",
                backstory="""You are a meticulous research specialist who excels at gathering
                all relevant data before making recommendations. You always search knowledge bases
                first to understand policies, then gather customer and product data systematically.""",
                tools=crewai_tools,
                verbose=True,
                llm=llm
            )

            analysis_agent = Agent(
                role="Product Analysis Specialist",
                goal="Evaluate products, calculate discounts, and optimize recommendations within budget",
                backstory="""You are an expert product analyst who evaluates customer needs
                against available products, calculates accurate pricing with discounts, and
                ensures all recommendations fit within budget constraints.""",
                tools=crewai_tools,
                verbose=True,
                llm=llm
            )

            communication_agent = Agent(
                role="Customer Communication Specialist",
                goal="Synthesize research and analysis into clear, friendly customer responses",
                backstory="""You are a customer service expert who creates warm, professional
                responses that address all customer questions comprehensively. You always
                explicitly state final prices and budget compliance.""",
                tools=crewai_tools,
                verbose=True,
                llm=llm
            )

            # Create tasks for multi-agent workflow
            research_task = Task(
                description=f"""Research the following customer inquiry for customer {customer_id}:

{user_message}

Your research must include:
1. Search knowledge base for refund policy and product recommendations
2. Get customer profile and tier information
3. Retrieve order history, especially ORD-1234 status
4. Get product catalogs for laptops, monitors, and keyboards

Be thorough and gather all relevant data.""",
                expected_output="""Complete research report with:
- Knowledge base insights on refunds and product recommendations
- Customer profile and purchase history
- Order status for ORD-1234
- Available product options in all categories""",
                agent=research_agent
            )

            analysis_task = Task(
                description="""Analyze the research data and provide recommendations:

1. Determine refund status and next steps for ORD-1234
2. Recommend best laptop based on customer history and avoiding previous issues
3. Suggest compatible monitor and keyboard
4. Calculate year-to-date spending and applicable discounts
5. Ensure complete setup stays within $3000 budget

Provide specific product recommendations with exact pricing.""",
                expected_output="""Analysis report with:
- Refund status and timeline
- Specific laptop, monitor, keyboard recommendations with product IDs
- Detailed pricing breakdown with discounts
- Total cost confirmation within budget""",
                agent=analysis_agent,
                context=[research_task]
            )

            communication_task = Task(
                description="""Create a customer-friendly response based on the analysis.

Requirements:
- Address all 5 customer questions clearly
- Use warm, professional tone
- Include specific product names and prices
- MUST explicitly state: "$[final_price] within your $[budget_amount] budget"
- Provide clear next steps""",
                expected_output="""Complete customer response addressing:
1. Refund status for ORD-1234
2. Laptop recommendation with reasoning
3. Monitor and keyboard suggestions
4. YTD spending and discount eligibility
5. Total setup cost explicitly stating "$X within your $Y budget" """,
                agent=communication_agent,
                context=[research_task, analysis_task]
            )

            # Create crew and execute
            crew = Crew(
                agents=[research_agent, analysis_agent, communication_agent],
                tasks=[research_task, analysis_task, communication_task],
                verbose=False
            )

            result = crew.kickoff()

            # Extract response
            response_text = str(result)

            # Extract token usage from crew usage_metrics
            input_tokens = 0
            output_tokens = 0
            if hasattr(crew, "usage_metrics"):
                metrics = crew.usage_metrics
                input_tokens = getattr(metrics, "prompt_tokens", 0)
                output_tokens = getattr(metrics, "completion_tokens", 0)

            end_time = time.time()

            return AgentResult(
                success=True,
                response=response_text,
                latency=end_time - start_time,
                tool_calls=self._local_tool_log,
                token_usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
                timestamp=datetime.now(),
                metadata={
                    "framework": "crewai_multiagent",
                    "agent_count": 3,
                    "agents": ["research", "analysis", "communication"],
                    "task_count": 3,
                    "customer_id": customer_id
                }
            )

        except Exception as e:
            import traceback
            traceback.print_exc()

            return AgentResult(
                success=False,
                response=f"Error: {str(e)}",
                latency=time.time() - start_time,
                tool_calls=self._local_tool_log,
                token_usage={"input_tokens": 0, "output_tokens": 0},
                timestamp=datetime.now(),
                metadata={"error": str(e), "customer_id": customer_id}
            )
