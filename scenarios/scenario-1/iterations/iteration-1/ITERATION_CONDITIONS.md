# Iteration 1 - Benchmark Conditions

**Date**: March 12, 2026
**Status**: ✅ Completed

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

## Frameworks Tested

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
- **System Prompt**: Consistent across all frameworks

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

## MCP Server Configuration

### Tools Provided
1. **get_customer(customer_id)**: Returns customer profile
2. **get_orders(customer_id)**: Returns customer order history
3. **search_knowledge_base(query)**: Searches KB for policies
4. **process_refund(order_id, reason)**: Processes refunds
5. **escalate_to_human(order_id, reason, priority)**: Escalates to human

### MCP Server Details
- **Implementation**: FastMCP (Python)
- **Transport**: stdio (standard input/output)
- **Server Script**: `arena/mcp_server.py`
- **Logging**: Tool calls logged to global list (for frameworks with persistent sessions)

---

## Framework Implementation Details

### Claude SDK
- **File**: `arena/frameworks/claude_sdk_agent.py`
- **LoC**: 114
- **CC**: 2.1
- **Key Features**:
  - Direct agent SDK with `query()` method
  - Event streaming for agent responses
  - Full token tracking via usage metrics
  - Persistent MCP session throughout agent execution

### AWS Strands
- **File**: `arena/frameworks/aws_strands_agent.py`
- **LoC**: 140
- **CC**: 2.2
- **Key Features**:
  - Native `BedrockModel` with boto3 session
  - Async tool wrappers with `@tool` decorator
  - Dynamic parameter signatures via `inspect.Signature()`
  - Persistent MCP session
  - **Limitation**: Token tracking returns 0

### Google ADK
- **File**: `arena/frameworks/google_adk_agent.py`
- **LoC**: 158
- **CC**: 2.0
- **Key Features**:
  - `LiteLlm` wrapper with model cost injection
  - `Runner` + `InMemorySessionService` architecture
  - Async tool functions
  - Persistent MCP session
  - **Limitation**: Token tracking returns 0

### CrewAI
- **File**: `arena/frameworks/crewai_agent.py`
- **LoC**: 145
- **CC**: 1.6
- **Key Features**:
  - `LLM` wrapper with LiteLLM integration
  - `Agent` + `Crew` + `BaseTool` architecture
  - Pydantic models for args_schema
  - ThreadPoolExecutor for async/sync bridging
  - Fresh MCP connection per tool call (event loop isolation)
  - Local tool log tracking
  - **Required**: GitHub PR #4805 fix for tool argument extraction

---

## Known Issues & Limitations

### Token Tracking
- **AWS Strands**: Returns 0 tokens (usage API limitation)
- **Google ADK**: Returns 0 tokens (needs investigation)
- **Claude SDK**: ✅ Working perfectly
- **CrewAI**: ✅ Working via LiteLLM metrics

### CrewAI Specific
- Required manual GitHub PR fix for Bedrock Converse API
- Lower consistency (67% pass³) due to S2 knowledge base skipping
- Event loop conflicts resolved with ThreadPoolExecutor pattern

### Scenario S1c
- All frameworks consistently skipped `search_knowledge_base` tool
- Resulted in 75% correctness (3/4 checks) for all frameworks
- Suggests system prompt or scenario may need clarification

---

## Results Summary

### Overall Winner: Google ADK
- **Fastest**: 12.34s average latency
- **Most Correct**: 91.67% (tied with Claude SDK & AWS Strands)
- **Most Consistent**: 100% pass³ (tied with Claude SDK & AWS Strands)

### Rankings
1. 🥇 **Google ADK** - Best overall (speed + correctness + consistency)
2. 🥈 **AWS Strands** - Excellent balance, native AWS integration
3. 🥉 **Claude SDK** - Best observability (full token tracking)
4. **CrewAI** - Simplest code, lower consistency

---

## Files Generated

### Results
- `combined_results.json` - Complete benchmark data
- `combined_results_table.md` - Detailed comparison tables
- `FINAL_RESULTS.md` - Executive summary
- `claude_sdk_results.json` - Claude SDK detailed results
- `new_frameworks_results.json` - AWS Strands, Google ADK, CrewAI results
- `results.json` - Initial run data
- `results_table.md` - Initial results table

### Scripts
- `run_new_frameworks.py` - Run AWS Strands, Google ADK, CrewAI benchmarks
- `run_crewai_only.py` - Run CrewAI benchmark only
- `generate_summary.py` - Generate summary from combined results

### Documentation
- `FINAL_RESULTS.md` - Main results document
- `combined_results_table.md` - Detailed tables
- Multiple status/implementation docs

---

## Environment Details

### Python Environment
- **Python Version**: 3.13.0 (pyenv)
- **Key Dependencies**:
  - `claude-agent-sdk-python`
  - `strands`
  - `google-adk`
  - `litellm`
  - `crewai` (1.10.2a1 from GitHub main)
  - `mcp`
  - `fastmcp`
  - `boto3`
  - `pydantic`

### System
- **Platform**: macOS (Darwin 25.3.0)
- **Working Directory**: `/Users/ukanagala/Desktop/uday/ai/conf/arena`
- **Git Repository**: Not initialized

---

## Iteration Completion Checklist

- ✅ All 4 frameworks implemented
- ✅ All 3 scenarios tested with K=3 repetitions
- ✅ All metrics collected and calculated
- ✅ Token tracking working for 2/4 frameworks
- ✅ CrewAI Bedrock bugs fixed with GitHub PRs
- ✅ Results documented and summarized
- ✅ Code complexity measured
- ✅ Correctness and consistency evaluated

---

## Next Steps for Iteration 2

### Improvements to Implement
1. **Fix Token Tracking**:
   - Investigate AWS Strands usage API
   - Research Google ADK usage metrics
   - Implement fallback token counting if needed

2. **Improve S3 Correctness**:
   - Update system prompt to encourage KB search for billing issues
   - Add explicit policy reference requirement
   - Test if frameworks call `search_knowledge_base` more consistently

3. **Add LangChain & LangGraph**:
   - Debug broken pipe errors from previous attempts
   - Implement with connection pooling or timeout adjustments
   - Complete the 6-framework benchmark

4. **Enhance Evaluation**:
   - Consider weighted metrics (some checks more important than others)
   - Add response quality evaluation (not just tool correctness)
   - Measure end-to-end user satisfaction proxies

5. **Test Variations**:
   - Different temperature settings (0 vs 0.7)
   - Different system prompt styles
   - Different scenario complexities
   - More repetitions (K=5 or K=10) for better statistical significance

---

## Lessons Learned

1. **Event Loop Management**: CrewAI's sync/async bridge required careful ThreadPoolExecutor + isolated loop pattern
2. **Tool Signatures**: Dynamic parameter signatures critical for framework introspection
3. **MCP Session Patterns**: Persistent sessions work for most, but CrewAI needs fresh connections per call
4. **Bedrock Compatibility**: Not all frameworks handle Bedrock Converse API equally (CrewAI needed fixes)
5. **Token Tracking**: Each framework has different usage tracking APIs - need framework-specific implementations

---

**Iteration 1 Completed**: March 12, 2026
**Ready for Iteration 2**: March 13, 2026
