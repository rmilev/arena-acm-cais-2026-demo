#!/usr/bin/env python3
"""
Run Scenario-3 (S3) - Multi-Agent Product Investigation & Recommendation - Extended

This script tests all 6 frameworks on the complex multi-agent scenario:
1. Claude SDK (with Skill)
2. CrewAI (Multi-Agent)
3. Google ADK (Multi-Agent)
4. AWS Strands (Multi-Agent)
5. LangGraph (Multi-Agent)
6. LangChain (Multi-Agent)

Usage:
    python scripts/run_scenario3_extended.py 1  # Run iteration 1
    python scripts/run_scenario3_extended.py 2  # Run iteration 2
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arena.scenarios import SCENARIOS
from arena.evaluator import evaluate_scenario
from arena.metrics import measure_code_complexity, compute_step_efficiency, compute_cost, compute_consistency
from arena.frameworks.claude_sdk_agent import ClaudeSDKAdapter
from arena.frameworks.crewai_multiagent import CrewAIMultiAgent
from arena.frameworks.google_adk_multiagent import GoogleADKMultiAgent
from arena.frameworks.aws_strands_multiagent import AWSStrandsMultiAgent
from arena.frameworks.langgraph_multiagent import LangGraphMultiAgent
from arena.frameworks.langchain_multiagent import LangChainMultiAgent


def get_framework_file_path(framework_name: str) -> str:
    """Get the file path for a framework implementation."""
    mapping = {
        "Claude SDK (with Skill)": "arena/frameworks/claude_sdk_agent.py",
        "CrewAI (Multi-Agent)": "arena/frameworks/crewai_multiagent.py",
        "Google ADK (Multi-Agent)": "arena/frameworks/google_adk_multiagent.py",
        "AWS Strands (Multi-Agent)": "arena/frameworks/aws_strands_multiagent.py",
        "LangGraph (Multi-Agent)": "arena/frameworks/langgraph_multiagent.py",
        "LangChain (Multi-Agent)": "arena/frameworks/langchain_multiagent.py",
    }
    return mapping.get(framework_name, "")


def aggregate_framework_metrics(framework_name: str, results: list, scenario_name: str) -> dict:
    """Aggregate metrics across all runs for a framework."""
    import statistics

    # Code complexity metrics (same for all runs)
    code_path = get_framework_file_path(framework_name)
    code_metrics = measure_code_complexity(code_path) if code_path else {"lines_of_code": 0, "cyclomatic_complexity": 0}

    # Get successful runs only
    successful_runs = [r for r in results if r.get("success", False)]

    if not successful_runs:
        return {
            **code_metrics,
            "scenarios": {
                scenario_name: {
                    "median_latency": 0.0,
                    "median_input_tokens": 0,
                    "median_output_tokens": 0,
                    "median_cost_usd": 0.0,
                    "median_step_efficiency": 0.0,
                    "consistency_pass3": 0.0,
                    "per_run_correctness": []
                }
            }
        }

    # Extract values
    latencies = [r["latency"] for r in successful_runs]
    correctness_scores = [r["correctness"] / 100 for r in successful_runs]
    tool_counts = [r["tool_calls"] for r in successful_runs]

    input_tokens = []
    output_tokens = []
    step_efficiencies = []

    for r in successful_runs:
        # Token usage
        if "token_usage" in r and r["token_usage"]:
            input_tokens.append(r["token_usage"].get("input_tokens", 0))
            output_tokens.append(r["token_usage"].get("output_tokens", 0))

        # Step efficiency
        optimal_steps = {"S3": 8, "S2": 8, "S1c": 4, "S1b": 3, "S1": 3}.get(scenario_name, 8)
        actual_steps = r["tool_calls"]
        if actual_steps > 0:
            efficiency = min(optimal_steps / actual_steps, 1.0)
            step_efficiencies.append(efficiency)

    # Calculate medians
    median_latency = round(statistics.median(latencies), 2) if latencies else 0.0
    median_input = int(statistics.median(input_tokens)) if input_tokens else 0
    median_output = int(statistics.median(output_tokens)) if output_tokens else 0
    median_cost = round(compute_cost(median_input, median_output), 4) if (median_input or median_output) else 0.0
    median_efficiency = round(statistics.median(step_efficiencies), 2) if step_efficiencies else 0.0

    # Consistency (all 3 runs pass at 75%+)
    consistency = compute_consistency(correctness_scores if len(correctness_scores) == 3 else [0.0, 0.0, 0.0])

    return {
        **code_metrics,
        "scenarios": {
            scenario_name: {
                "median_latency": median_latency,
                "median_input_tokens": median_input,
                "median_output_tokens": median_output,
                "median_cost_usd": median_cost,
                "median_step_efficiency": median_efficiency,
                "consistency_pass3": consistency["consistency_pass3"],
                "per_run_correctness": [round(c, 2) for c in correctness_scores]
            }
        }
    }


def run_framework(framework_name: str, framework_class, scenario_name: str, run_number: int):
    """Run a single framework on the scenario."""
    print(f"\n{'='*80}")
    print(f"Framework: {framework_name} | Scenario: {scenario_name} | Run: {run_number}")
    print(f"{'='*80}")

    scenario = SCENARIOS[scenario_name]

    # Initialize agent
    # Claude SDK needs system_prompt, others use BaseAgent interface
    if framework_name == "Claude SDK (with Skill)":
        system_prompt = """You are a helpful AI assistant with access to customer service tools.
Help customers with their inquiries about orders, products, and account information."""
        agent = framework_class(system_prompt=system_prompt)
    else:
        # Multi-agent frameworks
        agent = framework_class()

    try:
        # Run the agent
        result = agent.run(
            user_message=scenario["user_message"],
            customer_id=scenario["customer_id"]
        )

        # Evaluate correctness
        correctness_score, criteria_results = evaluate_scenario(
            scenario_id=scenario_name,
            tool_log=result.tool_calls,
            final_response=result.response
        )

        # Print results
        print(f"\n✅ Success!")
        print(f"Correctness: {correctness_score:.1f}%")
        print(f"Latency: {result.latency:.2f}s")
        print(f"Tool Calls: {len(result.tool_calls)}")
        print(f"Tools Used: {', '.join(set(result.tool_calls))}")

        # Save results
        output_dir = Path(f"scenarios/scenario-3/iterations/iteration-{run_number}")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{framework_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')}_t5_r{run_number}.json"
        output_data = {
            "framework": framework_name,
            "scenario": scenario_name,
            "run_number": run_number,
            "timestamp": result.timestamp.isoformat(),
            "correctness_score": correctness_score,
            "latency": result.latency,
            "tool_calls": result.tool_calls,
            "tool_count": len(result.tool_calls),
            "unique_tools": list(set(result.tool_calls)),
            "token_usage": result.token_usage,
            "criteria_results": criteria_results,
            "response": result.response,
            "metadata": result.metadata
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Results saved to: {output_file}")

        return {
            "framework": framework_name,
            "correctness": correctness_score,
            "latency": result.latency,
            "tool_calls": len(result.tool_calls),
            "success": True
        }

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "framework": framework_name,
            "correctness": 0.0,
            "latency": 0.0,
            "tool_calls": 0,
            "success": False,
            "error": str(e)
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_scenario3_extended.py <iteration_number>")
        print("Example: python scripts/run_scenario3_extended.py 1")
        sys.exit(1)

    iteration = int(sys.argv[1])
    scenario_name = "S3"
    repetitions = 3  # Run each framework 3 times

    print("="*80)
    print(f"SCENARIO-3 EXTENDED BENCHMARK - ITERATION {iteration}")
    print(f"Scenario: {scenario_name} (Multi-Agent Product Investigation)")
    print(f"Frameworks: 6 (Claude SDK, CrewAI, Google ADK, AWS Strands, LangGraph, LangChain)")
    print(f"Repetitions: {repetitions} per framework")
    print(f"Total Runs: {6 * repetitions} (6 frameworks × {repetitions} runs)")
    print("="*80)

    frameworks = [
        ("Claude SDK (with Skill)", ClaudeSDKAdapter),
        ("CrewAI (Multi-Agent)", CrewAIMultiAgent),
        ("Google ADK (Multi-Agent)", GoogleADKMultiAgent),
        ("AWS Strands (Multi-Agent)", AWSStrandsMultiAgent),
        ("LangGraph (Multi-Agent)", LangGraphMultiAgent),
        ("LangChain (Multi-Agent)", LangChainMultiAgent)
    ]

    all_results = []
    start_time = time.time()

    for rep in range(1, repetitions + 1):
        print(f"\n\n{'#'*80}")
        print(f"REPETITION {rep}/{repetitions}")
        print(f"{'#'*80}")

        for framework_name, framework_class in frameworks:
            result = run_framework(framework_name, framework_class, scenario_name, iteration)
            result["repetition"] = rep
            all_results.append(result)

            # Brief pause between frameworks
            time.sleep(2)

    total_time = time.time() - start_time

    # Generate summary
    print(f"\n\n{'='*80}")
    print(f"ITERATION {iteration} SUMMARY - EXTENDED")
    print(f"{'='*80}")
    print(f"Total execution time: {total_time:.2f}s")
    print(f"\nFramework Results (averaged across {repetitions} runs):\n")

    # Calculate averages per framework
    framework_stats = {}
    for framework_name, _ in frameworks:
        fw_results = [r for r in all_results if r["framework"] == framework_name]
        if fw_results:
            avg_correctness = sum(r["correctness"] for r in fw_results) / len(fw_results)
            avg_latency = sum(r["latency"] for r in fw_results) / len(fw_results)
            avg_tools = sum(r["tool_calls"] for r in fw_results) / len(fw_results)
            success_rate = sum(1 for r in fw_results if r["success"]) / len(fw_results) * 100

            framework_stats[framework_name] = {
                "correctness": avg_correctness,
                "latency": avg_latency,
                "tools": avg_tools,
                "success_rate": success_rate
            }

            print(f"{framework_name:35} | Correctness: {avg_correctness:5.1f}% | "
                  f"Latency: {avg_latency:6.2f}s | Tools: {avg_tools:4.1f} | "
                  f"Success: {success_rate:5.1f}%")

    # Save iteration summary
    summary_dir = Path(f"scenarios/scenario-3/iterations/iteration-{iteration}")
    summary_file = summary_dir / f"ITERATION_{iteration}_EXTENDED_SUMMARY.md"

    with open(summary_file, 'w') as f:
        f.write(f"# Scenario-3 Extended Iteration {iteration} Summary\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Scenario**: S3 (Multi-Agent Product Investigation)\n")
        f.write(f"**Frameworks**: 6\n")
        f.write(f"**Repetitions**: {repetitions} per framework\n")
        f.write(f"**Total Runs**: {len(all_results)}\n")
        f.write(f"**Total Time**: {total_time:.2f}s\n\n")

        f.write("## Framework Performance\n\n")
        f.write("| Framework | Correctness | Latency | Tool Calls | Success Rate |\n")
        f.write("|-----------|-------------|---------|------------|-------------|\n")

        for framework_name in sorted(framework_stats.keys(), key=lambda x: framework_stats[x]["correctness"], reverse=True):
            stats = framework_stats[framework_name]
            f.write(f"| {framework_name} | {stats['correctness']:.1f}% | "
                   f"{stats['latency']:.2f}s | {stats['tools']:.1f} | "
                   f"{stats['success_rate']:.0f}% |\n")

        f.write("\n## Key Findings\n\n")
        f.write("- Multi-agent coordination effectiveness varies by framework\n")
        f.write("- Tool call efficiency is critical for performance\n")
        f.write("- Context passing between agents impacts correctness\n")
        f.write("- LangGraph and LangChain provide additional multi-agent patterns\n")

    print(f"\nSummary saved to: {summary_file}")

    # Generate comprehensive metrics JSON
    metrics_data = {}
    for framework_name, _ in frameworks:
        fw_results = [r for r in all_results if r["framework"] == framework_name]
        fw_metrics = aggregate_framework_metrics(framework_name, fw_results, scenario_name)
        # Use snake_case key
        key = framework_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        metrics_data[key] = fw_metrics

    metrics_file = summary_dir / f"ITERATION_{iteration}_METRICS.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)

    print(f"Metrics saved to: {metrics_file}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
