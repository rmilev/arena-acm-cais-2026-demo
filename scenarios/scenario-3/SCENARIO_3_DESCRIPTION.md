# Scenario-3: Multi-Agent Product Investigation & Recommendation (S3)

**Type**: Complex Multi-Agent Collaboration
**Expected Duration**: 45-60 seconds
**Optimal Tool Calls**: 12-15
**Sub-Agents Required**: 3 specialized agents

---

## Overview

This scenario tests a framework's ability to decompose a complex customer request into subtasks handled by specialized sub-agents:

1. **Research Agent**: Gathers customer data and product information
2. **Analysis Agent**: Evaluates options and makes decisions
3. **Communication Agent**: Synthesizes findings into a customer response

---

## Test Case (S3)

### Customer Request

**Customer ID**: CUST-001 (Jane Smith, Premium Tier)

**Message**:
```
Hi, this is customer CUST-001. I'm looking to upgrade my home office setup.
I recently had issues with my laptop #ORD-1234, and I'm wondering:

1. What's the status of my refund?
2. Can you recommend a better laptop model based on my purchase history?
3. I also need a good monitor and keyboard to go with it
4. What's my total spending this year and do I qualify for any discounts?

I want reliable products and I'm willing to spend up to $3000 total.
Can you help me put together a complete setup?
```

---

## Expected Agent Workflow

### Sub-Agent 1: Research Agent
**Role**: Data gathering and retrieval

**Tasks**:
1. Look up customer profile → `get_customer(CUST-001)`
2. Retrieve order history → `get_orders(CUST-001)`
3. Search for refund policy → `search_knowledge_base("refund status")`
4. Search for product recommendations → `search_knowledge_base("laptop recommendations")`
5. Search for premium discounts → `search_knowledge_base("premium benefits")`

**Expected Tools**: 5 calls
- `get_customer` (1x)
- `get_orders` (1x)
- `search_knowledge_base` (3x with different queries)

**Output**: Structured data about customer, orders, and policies

---

### Sub-Agent 2: Analysis Agent
**Role**: Decision making and evaluation

**Tasks**:
1. Analyze order history to identify patterns
2. Calculate total spending YTD
3. Check refund eligibility for ORD-1234
4. Evaluate product needs based on previous issues
5. Determine budget allocation (laptop: $2000, monitor: $600, keyboard: $400)
6. Identify applicable discounts (premium tier benefits)

**Expected Tools**: 2-3 calls
- `get_orders` (if not cached from Research Agent)
- `search_knowledge_base` ("product comparisons")

**Output**: Recommendation matrix with justifications

---

### Sub-Agent 3: Communication Agent
**Role**: Customer response synthesis

**Tasks**:
1. Address refund status for ORD-1234
2. Present laptop recommendations with reasoning
3. Suggest complementary products (monitor, keyboard)
4. Summarize spending and discount eligibility
5. Provide clear next steps

**Expected Tools**: 1-2 calls
- `search_knowledge_base` ("how to order")
- Optional: `escalate_to_human` (if complex pricing needed)

**Output**: Comprehensive, personalized customer response

---

## MCP Tools Required

All existing tools from Scenario 1-2, plus:

### New Tools for Scenario-3:

```python
@mcp.tool()
def get_product_catalog(category: str) -> str:
    """Get product catalog for a category (laptops, monitors, keyboards)"""
    # Returns product list with specs and prices

@mcp.tool()
def calculate_discount(customer_id: str, total_amount: float) -> str:
    """Calculate applicable discounts for a customer"""
    # Returns discount information based on tier and spending

@mcp.tool()
def check_inventory(product_id: str) -> str:
    """Check product availability"""
    # Returns stock status and estimated delivery
```

---

## Correctness Criteria

### Research Phase (30 points)
- ✅ Looked up customer profile: `get_customer` called (5 pts)
- ✅ Retrieved order history: `get_orders` called (5 pts)
- ✅ Searched for refund info: `search_knowledge_base` with "refund" (5 pts)
- ✅ Searched for products: `search_knowledge_base` with "laptop" or "product" (5 pts)
- ✅ Searched for discounts: `search_knowledge_base` with "premium" or "discount" (5 pts)
- ✅ Used new catalog tool: `get_product_catalog` called (5 pts)

### Analysis Phase (25 points)
- ✅ Confirmed refund eligibility: Mentions ORD-1234 refund status (8 pts)
- ✅ Calculated spending: References customer's order history/spending (7 pts)
- ✅ Budget allocation: Provides breakdown for each product category (5 pts)
- ✅ Identified discounts: Mentions premium tier benefits (5 pts)

### Communication Phase (25 points)
- ✅ Addressed all 4 questions: Covers refund, laptop, accessories, spending (10 pts)
- ✅ Provided specific recommendations: Names specific products (5 pts)
- ✅ Included pricing: Shows total cost within $3000 budget (5 pts)
- ✅ Clear next steps: Explains how to proceed with purchase (5 pts)

### Multi-Agent Coordination (20 points)
- ✅ Logical task decomposition: Tasks distributed appropriately (10 pts)
- ✅ Information flow: Data passed correctly between agents (5 pts)
- ✅ No redundant calls: Efficient tool usage (5 pts)

**Total**: 100 points

**Scoring**:
- 90-100: Excellent multi-agent coordination
- 75-89: Good coordination with minor gaps
- 60-74: Adequate but inefficient
- <60: Poor coordination or missing components

---

## Key Challenges

1. **Agent Coordination**: Proper decomposition into specialized subtasks
2. **Context Sharing**: Passing data between sub-agents efficiently
3. **Tool Efficiency**: Avoiding redundant API calls across agents
4. **Response Synthesis**: Combining insights from multiple agents coherently
5. **Budget Constraints**: Respecting the $3000 total budget

---

## Framework Implementation Notes

### Claude SDK (with Skills & Sub-Agents)
- Use `Agent` class with specialized roles
- Implement coordinator agent that delegates to sub-agents
- Use context passing between agents

### CrewAI
- Define 3 Crew members (Research, Analysis, Communication)
- Use sequential or hierarchical process
- Define tasks for each crew member

### Google ADK
- Use multiple agent instances with different prompts
- Implement message passing between agents
- Use coordinator pattern

### AWS Strands
- Use Strands multi-agent orchestration
- Define agent roles and communication patterns
- Implement workflow with parallel execution where possible

---

## Expected Performance

| Framework | Correctness | Latency | Sub-Agents | Tool Calls |
|-----------|-------------|---------|------------|------------|
| Claude SDK | 85-95% | 45-55s | 3 | 12-14 |
| CrewAI | 80-90% | 50-60s | 3 | 13-15 |
| Google ADK | 75-85% | 40-50s | 3 | 11-13 |
| AWS Strands | 75-85% | 45-55s | 3 | 12-14 |

---

## Scenario Location

```
scenarios/
└── scenario-3/
    ├── SCENARIO_3_DESCRIPTION.md (this file)
    ├── iterations/
    │   └── iteration-1/
    │       ├── claude_sdk_t5_r1.json
    │       ├── crewai_t5_r1.json
    │       ├── google_adk_t5_r1.json
    │       └── aws_strands_t5_r1.json
    └── SCENARIO_3_RESULTS.md
```

---

**Status**: Ready for Implementation
**Created**: March 13, 2026
**Test Iterations**: 0 (to be run)
