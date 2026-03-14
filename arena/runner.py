"""Arena benchmark runner."""
import time
import json
import os
import sys
from datetime import datetime
from statistics import median
from pathlib import Path

from arena.scenarios import SYSTEM_PROMPT, SCENARIOS
from arena.metrics import (
    measure_code_complexity,
    compute_step_efficiency,
    compute_cost,
    compute_consistency,
)
from arena.evaluator import evaluate_scenario

# Import all framework adapters
from arena.frameworks.claude_sdk_agent import ClaudeSDKAdapter
from arena.frameworks.aws_strands_agent import AWSStrandsAdapter
from arena.frameworks.langchain_agent import LangChainAdapter
from arena.frameworks.langgraph_agent import LangGraphAdapter
from arena.frameworks.crewai_agent import CrewAIAdapter
from arena.frameworks.google_adk_agent import GoogleADKAdapter


FRAMEWORKS = {
    "claude_sdk": ClaudeSDKAdapter,
    "aws_strands": AWSStrandsAdapter,
    "langchain": LangChainAdapter,
    "langgraph": LangGraphAdapter,
    "crewai": CrewAIAdapter,
    "google_adk": GoogleADKAdapter,
}

FRAMEWORK_FILES = {
    "claude_sdk": "arena/frameworks/claude_sdk_agent.py",
    "aws_strands": "arena/frameworks/aws_strands_agent.py",
    "langchain": "arena/frameworks/langchain_agent.py",
    "langgraph": "arena/frameworks/langgraph_agent.py",
    "crewai": "arena/frameworks/crewai_agent.py",
    "google_adk": "arena/frameworks/google_adk_agent.py",
}

K = 3  # repetitions per scenario


def run_single_scenario(adapter, scenario_id: str, user_message: str):
    """Run one scenario and return metrics."""
    # Start MCP server
    adapter.start_mcp_server()
    adapter.connect_to_mcp()

    # Reset tool log
    import subprocess
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import asyncio

    async def reset_log():
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["arena/mcp_server.py"],
            env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.call_tool("arena_reset_log", {})

    asyncio.run(reset_log())

    # Run agent with timing
    start = time.perf_counter()
    final_response = adapter.run_agent(user_message)
    elapsed = time.perf_counter() - start
    latency_seconds = round(elapsed, 2)

    # Get token usage
    token_usage = adapter.get_token_usage()
    input_tokens = token_usage["input_tokens"]
    output_tokens = token_usage["output_tokens"]

    # Get tool log
    async def get_log():
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["arena/mcp_server.py"],
            env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("arena_get_log", {})
                return json.loads(result.content[0].text)

    tool_log = asyncio.run(get_log())

    # Stop MCP server
    adapter.stop_mcp_server()

    # Evaluate correctness
    correctness_result = evaluate_scenario(scenario_id, tool_log, final_response)

    # Compute step efficiency
    step_efficiency = compute_step_efficiency(scenario_id, tool_log)

    # Compute cost
    model_key = "gemini_flash" if "google" in adapter.__class__.__name__.lower() else "claude_sonnet"
    cost_usd = compute_cost(input_tokens, output_tokens, model_key)

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "tool_calls": tool_log,
        "num_tool_calls": len(tool_log),
        "optimal_tool_calls": step_efficiency["optimal_tool_calls"],
        "step_efficiency_ratio": step_efficiency["step_efficiency_ratio"],
        "latency_seconds": latency_seconds,
        "correctness_score": correctness_result["correctness_score"],
        "correctness_details": correctness_result["correctness_details"],
        "cost_usd": cost_usd,
        "final_response": final_response,
    }


def run_framework_benchmark(framework_name: str):
    """Run all scenarios for a framework (3 repetitions each)."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {framework_name}")
    print(f"{'='*60}")

    adapter_class = FRAMEWORKS[framework_name]
    results = {"scenarios": {}}

    for scenario_id, scenario_data in SCENARIOS.items():
        print(f"\n--- Scenario {scenario_id} ---")
        runs = []

        for rep in range(1, K + 1):
            print(f"  Run {rep}/{K}...", end=" ", flush=True)
            try:
                adapter = adapter_class(SYSTEM_PROMPT)
                run_result = run_single_scenario(
                    adapter,
                    scenario_id,
                    scenario_data["user_message"]
                )
                runs.append(run_result)
                print(f"✓ (correctness: {run_result['correctness_score']:.2f})")
            except Exception as e:
                print(f"✗ Error: {e}")
                # Record failure
                runs.append({
                    "error": str(e),
                    "correctness_score": 0.0,
                    "latency_seconds": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0,
                })

        # Compute aggregates (median for latency/tokens/cost)
        if runs:
            correctness_scores = [r.get("correctness_score", 0) for r in runs]
            consistency = compute_consistency(correctness_scores)

            # Median values
            latencies = [r.get("latency_seconds", 0) for r in runs]
            input_tokens_list = [r.get("input_tokens", 0) for r in runs]
            output_tokens_list = [r.get("output_tokens", 0) for r in runs]
            costs = [r.get("cost_usd", 0) for r in runs]

            results["scenarios"][scenario_id] = {
                "per_run_results": runs,
                "median_latency": round(median(latencies), 2) if latencies else 0,
                "median_input_tokens": int(median(input_tokens_list)) if input_tokens_list else 0,
                "median_output_tokens": int(median(output_tokens_list)) if output_tokens_list else 0,
                "median_cost_usd": round(median(costs), 4) if costs else 0,
                "consistency_pass3": consistency["consistency_pass3"],
                "per_run_correctness": consistency["per_run_correctness"],
            }

    # Measure code complexity (Metric 1)
    filepath = FRAMEWORK_FILES[framework_name]
    complexity = measure_code_complexity(filepath)
    results["lines_of_code"] = complexity["lines_of_code"]
    results["cyclomatic_complexity"] = complexity["cyclomatic_complexity"]

    return results


def generate_results_json(all_results: dict):
    """Generate results.json."""
    output = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "model_config": {
            "claude_model": "claude-sonnet-4-20250514",
            "gemini_model": "gemini-2.0-flash",
            "temperature": 0,
            "pricing": {
                "claude_sonnet_input_per_M": 3.00,
                "claude_sonnet_output_per_M": 15.00,
                "gemini_flash_input_per_M": 0.10,
                "gemini_flash_output_per_M": 0.40,
            }
        },
        "frameworks": all_results
    }

    with open("arena/results/results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n✓ Generated: arena/results/results.json")


def generate_results_table(all_results: dict):
    """Generate results_table.md."""
    lines = []
    lines.append("# Arena Benchmark Results\n")
    lines.append("## Summary Table\n")

    # Header
    lines.append("| Framework | LoC | CC | Avg Tokens (In / Out) | Avg Step Eff Ratio | Avg Latency (s) | Avg Correct | Avg Cost ($) | Avg pass³ |")
    lines.append("|-----------|-----|----|-----------------------|--------------------|-----------------| ------------|--------------|-----------|")

    # Rows
    for fw_name, fw_results in all_results.items():
        loc = fw_results.get("lines_of_code", 0)
        cc = fw_results.get("cyclomatic_complexity", 0)

        scenarios = fw_results.get("scenarios", {})
        if not scenarios:
            continue

        # Average across scenarios
        avg_input = sum(s["median_input_tokens"] for s in scenarios.values()) / len(scenarios)
        avg_output = sum(s["median_output_tokens"] for s in scenarios.values()) / len(scenarios)
        avg_latency = sum(s["median_latency"] for s in scenarios.values()) / len(scenarios)
        avg_cost = sum(s["median_cost_usd"] for s in scenarios.values()) / len(scenarios)
        avg_pass3 = sum(s["consistency_pass3"] for s in scenarios.values()) / len(scenarios)

        # Average correctness across all runs
        all_correctness = []
        for s in scenarios.values():
            all_correctness.extend(s["per_run_correctness"])
        avg_correct = sum(all_correctness) / len(all_correctness) if all_correctness else 0

        # Average step efficiency
        all_step_eff = []
        for s in scenarios.values():
            for run in s["per_run_results"]:
                all_step_eff.append(run.get("step_efficiency_ratio", 1.0))
        avg_step_eff = sum(all_step_eff) / len(all_step_eff) if all_step_eff else 1.0

        lines.append(
            f"| {fw_name} | {loc} | {cc:.1f} | {int(avg_input)} / {int(avg_output)} | "
            f"{avg_step_eff:.2f} | {avg_latency:.2f} | {avg_correct:.2f} | {avg_cost:.4f} | {avg_pass3:.2f} |"
        )

    with open("arena/results/results_table.md", "w") as f:
        f.write("\n".join(lines))

    print("✓ Generated: arena/results/results_table.md")


def main():
    """Run full benchmark."""
    print("\n" + "="*60)
    print("ARENA: Agent Framework Comparison Benchmark")
    print("="*60)

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    all_results = {}

    for fw_name in FRAMEWORKS.keys():
        try:
            results = run_framework_benchmark(fw_name)
            all_results[fw_name] = results
        except Exception as e:
            print(f"\n✗ Framework {fw_name} failed: {e}")
            all_results[fw_name] = {"error": str(e)}

    # Generate outputs
    generate_results_json(all_results)
    generate_results_table(all_results)

    print("\n" + "="*60)
    print("Benchmark complete!")
    print("="*60)


if __name__ == "__main__":
    main()
