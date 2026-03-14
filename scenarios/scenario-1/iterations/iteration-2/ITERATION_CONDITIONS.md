# Iteration 2 - Benchmark Conditions

**Date**: March 13, 2026
**Status**: 🔄 In Progress

---

## Test Configuration

### Model Configuration
- **Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Provider**: AWS Bedrock
- **Region**: `us-east-1`
- **AWS Profile**: `prod-tools`
- **Temperature**: 0
- **Environment Variable**: `CLAUDE_CODE_USE_BEDROCK=1`

### Pricing (for cost calculations)
- **Input tokens**: $3.00 per million tokens
- **Output tokens**: $15.00 per million tokens

---

## Frameworks to Test

| Framework | Version | Integration Method |
|-----------|---------|-------------------|
| **Claude SDK** | claude-agent-sdk-python | Direct agent SDK with AWS Bedrock |
| **AWS Strands** | strands | Native BedrockModel with boto3 |
| **Google ADK** | google-adk | LiteLlm wrapper + Runner architecture |
| **CrewAI** | 1.10.2a1 (main branch) | LLM wrapper with GitHub PR fixes |

---

## Benchmark Parameters

### Scenarios
- **S1**: Damaged Laptop Refund
- **S2**: Shipping Address Change
- **S3**: Billing Dispute / Double Charge

### Test Parameters
- **Repetitions (K)**: 3 per scenario per framework
- **Total Test Runs**: 36 (4 frameworks × 3 scenarios × 3 repetitions)
- **System Prompt**: Consistent across all frameworks (same as Iteration 1)

### Metrics Measured
1. **Lines of Code (LoC)**: Implementation complexity
2. **Cyclomatic Complexity (CC)**: Code complexity metric
3. **Latency**: Time to complete scenario (seconds)
4. **Token Usage**: Input and output tokens consumed
5. **Cost**: USD cost based on token usage
6. **Step Efficiency**: Ratio of actual tools called to optimal tools
7. **Correctness**: Percentage of required actions completed correctly
8. **Consistency (Pass³)**: Whether all 3 runs produced same correctness score

---

## System Prompt

```
You are a customer support agent for TechCorp, an electronics retailer.

Your role:
- Help customers with orders, refunds, and inquiries
- Use provided tools to look up customer and order information
- Escalate complex issues to human agents when appropriate
- Always be polite, professional, and helpful

Available tools:
- get_customer: Look up customer profile by ID
- get_orders: Retrieve order history for a customer
- search_knowledge_base: Search internal knowledge base for policies
- process_refund: Process a refund for an eligible order
- escalate_to_human: Escalate issue to human support agent
```

---

## Changes from Iteration 1

### None - Exact Replication
This iteration uses identical conditions to Iteration 1 to:
1. Validate consistency of results across different runs
2. Measure variance in latency and correctness
3. Establish baseline for statistical significance
4. Ensure frameworks behave consistently over time

### What Remains the Same
- ✅ Same model and configuration
- ✅ Same frameworks and versions
- ✅ Same scenarios and test parameters
- ✅ Same system prompt
- ✅ Same MCP server tools
- ✅ Same evaluation metrics

---

## Expected Outcomes

### Hypothesis
Results should be similar to Iteration 1 with minor variance:
- **Latency**: ±10-20% variance expected due to network/API variability
- **Token Usage**: Should be identical (temperature=0)
- **Correctness**: Should be identical or very close (deterministic model)
- **Tool Calls**: Should match exactly (temperature=0)

### Comparison Metrics
- Mean and standard deviation across both iterations
- Percentage change in key metrics
- Consistency validation (do frameworks produce same results?)

---

## MCP Server Configuration

### Tools Provided (Same as Iteration 1)
1. **get_customer(customer_id)**: Returns customer profile
2. **get_orders(customer_id)**: Returns customer order history
3. **search_knowledge_base(query)**: Searches KB for policies
4. **process_refund(order_id, reason)**: Processes refunds
5. **escalate_to_human(order_id, reason, priority)**: Escalates to human

### MCP Server Details
- **Implementation**: FastMCP (Python)
- **Transport**: stdio (standard input/output)
- **Server Script**: `arena/mcp_server.py`
- **Logging**: Tool calls logged to global list

---

## Framework Implementation Details

### Implementation Files (No Changes)
- **Claude SDK**: `arena/frameworks/claude_sdk_agent.py` (114 LoC, CC 2.1)
- **AWS Strands**: `arena/frameworks/aws_strands_agent.py` (140 LoC, CC 2.2)
- **Google ADK**: `arena/frameworks/google_adk_agent.py` (158 LoC, CC 2.0)
- **CrewAI**: `arena/frameworks/crewai_agent.py` (145 LoC, CC 1.6)

---

## Iteration 1 Results (Baseline)

### Overall Rankings
1. 🥇 **Google ADK** - 12.34s latency, 91.67% correctness, 100% consistency
2. 🥈 **AWS Strands** - 13.73s latency, 91.67% correctness, 100% consistency
3. 🥉 **Claude SDK** - 13.94s latency, 91.67% correctness, 100% consistency
4. **CrewAI** - 13.94s latency, 80.67% correctness, 67% consistency

### Iteration 1 Detailed Results

#### Scenario S1
| Framework | Latency | Tokens (In/Out) | Cost | Correctness | Pass³ |
|-----------|---------|-----------------|------|-------------|-------|
| Google ADK | 10.83s | 0*/0* | $0.00* | 100% | 1.00 |
| AWS Strands | 10.83s | 0*/0* | $0.00* | 100% | 1.00 |
| Claude SDK | 12.03s | 4,492/383 | $0.0192 | 100% | 1.00 |
| CrewAI | 13.16s | 4,687/444 | $0.0207 | 100% | 1.00 |

#### Scenario S1b
| Framework | Latency | Tokens (In/Out) | Cost | Correctness | Pass³ |
|-----------|---------|-----------------|------|-------------|-------|
| CrewAI | 11.60s | 2,794/465 | $0.0154 | 67% | 0.00 |
| Google ADK | 13.09s | 0*/0* | $0.00* | 100% | 1.00 |
| AWS Strands | 13.90s | 0*/0* | $0.00* | 100% | 1.00 |
| Claude SDK | 15.19s | 4,494/511 | $0.0211 | 100% | 1.00 |

#### Scenario S1c
| Framework | Latency | Tokens (In/Out) | Cost | Correctness | Pass³ |
|-----------|---------|-----------------|------|-------------|-------|
| Google ADK | 13.10s | 0*/0* | $0.00* | 75% | 1.00 |
| Claude SDK | 14.60s | 4,578/537 | $0.0218 | 75% | 1.00 |
| AWS Strands | 16.46s | 0*/0* | $0.00* | 75% | 1.00 |
| CrewAI | 17.05s | 4,728/767 | $0.0257 | 75% | 1.00 |

*Token tracking limitation

---

## Run Instructions

### Setup
```bash
cd /Users/ukanagala/Desktop/uday/ai/conf/arena
source .env  # or set environment variables
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_PROFILE=prod-tools
export AWS_DEFAULT_REGION=us-east-1
```

### Run Benchmarks
```bash
# Run all frameworks
python scripts/run_new_frameworks.py

# Or run individually
python scripts/run_crewai_only.py
```

### Generate Results
```bash
# Generate summary
python scripts/generate_summary.py

# Results will be saved to:
# - iterations/iteration-2/results/
```

---

## Expected Deliverables

### Results Files
- `combined_results.json` - Complete benchmark data
- `combined_results_table.md` - Detailed comparison tables
- `FINAL_RESULTS.md` - Executive summary
- Individual framework result files

### Comparison Analysis
- `ITERATION_COMPARISON.md` - Compare Iteration 1 vs Iteration 2
  - Latency variance analysis
  - Token usage consistency
  - Correctness stability
  - Statistical significance tests

---

## Success Criteria

✅ **Benchmark Complete** if:
1. All 4 frameworks run successfully (36 total runs)
2. All results collected and saved
3. Comparison with Iteration 1 documented
4. Variance analysis completed

⚠️ **Review Required** if:
- Latency variance > 30% for any framework
- Correctness scores differ by > 10%
- Tool calling patterns change significantly
- Token usage differs (should be identical at temperature=0)

---

## Notes

- This is a **replication study** - no code changes between iterations
- Purpose is to establish baseline variance and validate consistency
- Results will inform whether statistical significance can be claimed
- If results are stable, future iterations can test variations

---

**Iteration 2 Started**: March 13, 2026
**Expected Completion**: March 13, 2026
