# Scenario-3: Multi-Agent Product Investigation & Recommendation

**Status**: ✅ Implementation Complete, Ready for Testing
**Created**: March 13, 2026
**Test Case**: S3

---

## Overview

Scenario-3 introduces **multi-agent collaboration** where specialized sub-agents work together to handle a complex customer request involving product recommendations, refund status, spending analysis, and discount calculations.

This scenario tests:
- **Agent orchestration**: Coordinating multiple specialized agents
- **Context sharing**: Passing information between agents efficiently
- **Tool efficiency**: Avoiding redundant API calls across agents
- **Response synthesis**: Combining insights from multiple agents coherently
- **Complex decision-making**: Balancing budget, preferences, and constraints

---

## Multi-Agent Architecture

### Framework Implementations

#### 1. **Claude SDK** (`claude_sdk_multiagent.py`)
- **Pattern**: Coordinator with 3 specialists
- **Agents**:
  - Coordinator: Orchestrates workflow
  - Research: Data gathering
  - Analysis: Evaluation & recommendations
  - Communication: Response synthesis
- **Strength**: Strong context management between agents

#### 2. **CrewAI** (`crewai_multiagent.py`)
- **Pattern**: Crew with sequential process
- **Agents**:
  - Research Specialist
  - Analysis Specialist
  - Communication Specialist
- **Process**: Sequential with context passing
- **Strength**: Built-in multi-agent orchestration

#### 3. **Google ADK** (`google_adk_multiagent.py`)
- **Pattern**: Multiple agent instances with message passing
- **Agents**: 3 specialized agent instances
- **Coordination**: Manual orchestration with data passing
- **Strength**: Fast execution with parallel capability

#### 4. **AWS Strands** (`aws_strands_multiagent.py`)
- **Pattern**: Multi-strand orchestration
- **Strands**:
  - Research Strand
  - Analysis Strand
  - Communication Strand
- **Strength**: Native AWS integration

---

## Test Case: S3

### Customer Request

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

### Expected Workflow

**Phase 1 - Research Agent**:
1. Get customer profile (CUST-001)
2. Retrieve order history
3. Search KB: refund policy
4. Search KB: laptop recommendations
5. Search KB: premium benefits
6. Get product catalog: laptops
7. Get product catalog: monitors
8. Get product catalog: keyboards

**Phase 2 - Analysis Agent**:
1. Confirm refund status for ORD-1234
2. Calculate YTD spending
3. Evaluate laptop options (considering previous issue)
4. Select complementary monitor + keyboard
5. Calculate total cost
6. Apply discount calculation
7. Verify within $3000 budget

**Phase 3 - Communication Agent**:
1. Address all 4 questions
2. Present recommendations with justifications
3. Show pricing breakdown with discounts
4. Provide next steps

---

## MCP Tools

### Original Tools (5)
- `get_customer` - Customer profile lookup
- `get_orders` - Order history retrieval
- `search_knowledge_base` - KB search
- `process_refund` - Refund processing
- `escalate_to_human` - Escalation

### New Tools for S3 (3)
- `get_product_catalog` - Product catalog by category (laptops, monitors, keyboards, bundles)
- `calculate_discount` - Discount calculation based on tier and spending
- `check_inventory` - Product availability and delivery estimates

**MCP Server**: `arena/mcp_server_v2.py` (extended with 8 total tools)

---

## Correctness Criteria (100 points)

### Research Phase (30 points)
- ✅ Looked up customer profile: 5 pts
- ✅ Retrieved order history: 5 pts
- ✅ Searched refund info: 5 pts
- ✅ Searched products: 5 pts
- ✅ Searched discounts: 5 pts
- ✅ Used product catalog: 5 pts

### Analysis Phase (25 points)
- ✅ Confirmed refund status: 8 pts
- ✅ Calculated spending: 7 pts
- ✅ Budget allocation: 5 pts
- ✅ Identified discounts: 5 pts

### Communication Phase (25 points)
- ✅ Addressed all 4 questions: 10 pts
- ✅ Provided specific recommendations: 5 pts
- ✅ Included pricing: 5 pts
- ✅ Clear next steps: 5 pts

### Multi-Agent Coordination (20 points)
- ✅ Logical task decomposition: 10 pts
- ✅ Information flow between agents: 5 pts
- ✅ No redundant calls: 5 pts

**Total**: 100 points

**Grading**:
- 90-100: Excellent multi-agent coordination
- 75-89: Good coordination with minor gaps
- 60-74: Adequate but inefficient
- <60: Poor coordination or missing components

---

## Running the Benchmark

### Start MCP Server V2

```bash
cd arena
python -m arena.mcp_server_v2
```

### Run Iteration 1

```bash
cd /Users/ukanagala/Desktop/uday/ai/conf/arena
python scripts/run_scenario3.py 1
```

### View Results

```bash
cat scenarios/scenario-3/iterations/iteration-1/ITERATION_1_SUMMARY.md
```

---

## Expected Performance

| Framework | Correctness | Latency | Sub-Agents | Tool Calls |
|-----------|-------------|---------|------------|------------|
| Claude SDK | 85-95% | 45-55s | 3 | 12-14 |
| CrewAI | 80-90% | 50-60s | 3 | 13-15 |
| Google ADK | 75-85% | 40-50s | 3 | 11-13 |
| AWS Strands | 75-85% | 45-55s | 3 | 12-14 |

**Key Insights**:
- Context management critical for multi-agent coordination
- Tool call efficiency varies significantly by framework
- Sequential vs. parallel agent execution impacts latency
- Communication between agents is a performance bottleneck

---

## File Structure

```
scenarios/scenario-3/
├── README.md                          # This file
├── SCENARIO_3_DESCRIPTION.md          # Detailed scenario spec
├── iterations/
│   ├── iteration-1/
│   │   ├── claude_sdk_multiagent_t5_r1.json
│   │   ├── crewai_multiagent_t5_r1.json
│   │   ├── google_adk_multiagent_t5_r1.json
│   │   ├── aws_strands_multiagent_t5_r1.json
│   │   └── ITERATION_1_SUMMARY.md
│   └── iteration-2/
│       └── ...
└── SCENARIO_3_RESULTS.md             # Final analysis (after testing)

arena/frameworks/
├── claude_sdk_multiagent.py          # Claude SDK implementation
├── crewai_multiagent.py              # CrewAI implementation
├── google_adk_multiagent.py          # Google ADK implementation
└── aws_strands_multiagent.py         # AWS Strands implementation

arena/
├── mcp_server_v2.py                  # Extended MCP server (8 tools)
└── scenarios.py                      # Updated with S3

scripts/
└── run_scenario3.py                  # Benchmark runner
```

---

## Key Differences from Scenario-1 & Scenario-2

### Scenario-1 (S1/S1b/S1c)
- **Complexity**: Simple, single-issue
- **Tool Calls**: 3-4
- **Agent Type**: Single agent
- **Focus**: Basic competency

### Scenario-2 (S2)
- **Complexity**: Complex, multi-issue
- **Tool Calls**: 8
- **Agent Type**: Single agent with context management
- **Focus**: Context handling

### Scenario-3 (S3)
- **Complexity**: Very complex, multi-faceted
- **Tool Calls**: 12-15
- **Agent Type**: **Multiple specialized sub-agents**
- **Focus**: **Agent coordination and collaboration**

---

## Implementation Notes

### Claude SDK Multi-Agent
- Uses coordinator pattern with specialized agents
- Tool calls are efficiently distributed across agents
- Strong context passing between coordinator and specialists

### CrewAI Multi-Agent
- Leverages built-in Crew and Task abstractions
- Sequential process ensures data flows correctly
- Agent tools are partitioned by role

### Google ADK Multi-Agent
- Manual orchestration with explicit phases
- Each agent instance handles specific responsibility
- Data passed via structured prompts

### AWS Strands Multi-Agent
- Uses Strands library (or fallback to manual)
- Each strand has specific tools and instructions
- Orchestration mode controls execution order

---

## Next Steps

1. **Start MCP Server V2**: `python -m arena.mcp_server_v2`
2. **Run Iteration 1**: `python scripts/run_scenario3.py 1`
3. **Analyze Results**: Review correctness scores and agent coordination
4. **Run Iteration 2**: Test reproducibility
5. **Compare with Scenario-1/2**: How do multi-agent systems perform vs single agents?

---

## Research Questions

1. **Do multi-agent systems outperform single agents on complex tasks?**
2. **Which orchestration pattern is most effective? (sequential, parallel, hierarchical)**
3. **How much overhead does agent coordination introduce?**
4. **Are tool calls distributed efficiently across agents?**
5. **Does context get lost when passing between agents?**

---

**Status**: ✅ Ready for Testing
**Last Updated**: March 13, 2026
