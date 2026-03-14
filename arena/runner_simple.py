"""Arena benchmark runner.

Usage:
    # Full benchmark (all 6 frameworks, 3 scenarios, K=3 reps each = 54 runs)
    python -m arena.runner_simple

    # Specific frameworks only
    python -m arena.runner_simple --frameworks aws_strands crewai google_adk

    # Specific scenarios only
    python -m arena.runner_simple --scenarios T1 T4

    # Quick validation (K=1 rep, single scenario)
    python -m arena.runner_simple --quick

    # Custom repetitions
    python -m arena.runner_simple --reps 5
"""
import argparse
import json
import time
from statistics import median
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from arena.scenarios import SYSTEM_PROMPT, SCENARIOS
from arena.frameworks.claude_sdk_agent import ClaudeSDKAdapter
from arena.frameworks.langchain_agent import LangChainAdapter
from arena.frameworks.langgraph_agent import LangGraphAdapter
from arena.frameworks.aws_strands_agent import AWSStrandsAdapter
from arena.frameworks.crewai_agent import CrewAIAdapter
from arena.frameworks.google_adk_agent import GoogleADKAdapter
from arena.evaluator import evaluate_scenario
from arena.metrics import (
    measure_code_complexity,
    compute_step_efficiency,
    compute_cost,
    compute_consistency,
)


FRAMEWORKS = {
    "claude_sdk": {
        "adapter": ClaudeSDKAdapter,
        "file": "arena/frameworks/claude_sdk_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
    "langchain": {
        "adapter": LangChainAdapter,
        "file": "arena/frameworks/langchain_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
    "langgraph": {
        "adapter": LangGraphAdapter,
        "file": "arena/frameworks/langgraph_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
    "aws_strands": {
        "adapter": AWSStrandsAdapter,
        "file": "arena/frameworks/aws_strands_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
    "crewai": {
        "adapter": CrewAIAdapter,
        "file": "arena/frameworks/crewai_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
    "google_adk": {
        "adapter": GoogleADKAdapter,
        "file": "arena/frameworks/google_adk_agent.py",
        "model": "claude_sonnet",
        "status": "implemented"
    },
}

ALL_SCENARIOS = ["T1", "T4", "T5"]
DEFAULT_K = 3  # repetitions per scenario


def run_single_scenario(adapter_class, scenario_id: str):
    """Run one scenario once."""
    scenario = SCENARIOS[scenario_id]

    adapter = adapter_class(SYSTEM_PROMPT)
    adapter.start_mcp_server()
    adapter.connect_to_mcp()

    start = time.perf_counter()
    final_response = adapter.run_agent(scenario["user_message"])
    latency = time.perf_counter() - start

    usage = adapter.get_token_usage()
    tool_log = adapter.get_tool_log()
    adapter.stop_mcp_server()

    # Evaluate
    eval_result = evaluate_scenario(scenario_id, tool_log, final_response)
    step_eff = compute_step_efficiency(scenario_id, tool_log)
    cost = compute_cost(usage["input_tokens"], usage["output_tokens"], "claude_sonnet")

    return {
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "tool_calls": tool_log,
        "num_tool_calls": len(tool_log),
        "optimal_tool_calls": step_eff["optimal_tool_calls"],
        "step_efficiency_ratio": step_eff["step_efficiency_ratio"],
        "latency_seconds": round(latency, 2),
        "correctness_score": eval_result["correctness_score"],
        "correctness_details": eval_result["correctness_details"],
        "cost_usd": cost,
        "final_response": final_response[:200] + "..."
    }


def run_framework_benchmark(framework_name: str, scenarios: list[str], k: int):
    """Run selected scenarios for a framework (k reps each)."""
    fw = FRAMEWORKS[framework_name]

    if fw["status"] != "implemented":
        print(f"\n  {framework_name}: Not yet implemented, skipping")
        return {"status": "not_implemented"}

    print(f"\n{'='*70}")
    print(f"BENCHMARKING: {framework_name}")
    print(f"{'='*70}")

    results = {"scenarios": {}}

    for scenario_id in scenarios:
        print(f"\n--- Scenario {scenario_id} ---")
        runs = []

        for rep in range(1, k + 1):
            print(f"  Rep {rep}/{k}...", end=" ", flush=True)
            try:
                run_result = run_single_scenario(fw["adapter"], scenario_id)
                runs.append(run_result)
                print(f"  correctness={run_result['correctness_score']:.2f}  "
                      f"tokens={run_result['input_tokens']}/{run_result['output_tokens']}  "
                      f"latency={run_result['latency_seconds']}s  "
                      f"cost=${run_result['cost_usd']:.4f}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"  ERROR: {str(e)[:80]}")
                runs.append({"error": str(e), "correctness_score": 0.0})

        # Compute aggregates
        if runs:
            correctness_scores = [r.get("correctness_score", 0) for r in runs]
            consistency = compute_consistency(correctness_scores)

            latencies = [r.get("latency_seconds", 0) for r in runs if "latency_seconds" in r]
            input_tokens = [r.get("input_tokens", 0) for r in runs if "input_tokens" in r]
            output_tokens = [r.get("output_tokens", 0) for r in runs if "output_tokens" in r]
            costs = [r.get("cost_usd", 0) for r in runs if "cost_usd" in r]
            step_ratios = [r.get("step_efficiency_ratio", 1.0) for r in runs if "step_efficiency_ratio" in r]

            results["scenarios"][scenario_id] = {
                "per_run_results": runs,
                "median_latency": round(median(latencies), 2) if latencies else 0,
                "median_input_tokens": int(median(input_tokens)) if input_tokens else 0,
                "median_output_tokens": int(median(output_tokens)) if output_tokens else 0,
                "median_cost_usd": round(median(costs), 4) if costs else 0,
                "median_step_efficiency": round(median(step_ratios), 2) if step_ratios else 1.0,
                "consistency_pass3": consistency["consistency_pass3"],
                "per_run_correctness": consistency["per_run_correctness"],
            }

    # Code complexity
    if "file" in fw:
        complexity = measure_code_complexity(fw["file"])
        results["lines_of_code"] = complexity["lines_of_code"]
        results["cyclomatic_complexity"] = complexity["cyclomatic_complexity"]

    return results


def generate_results_json(all_results: dict):
    """Generate results.json."""
    output = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "model_config": {
            "claude_model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "temperature": 0,
            "pricing": {
                "claude_sonnet_input_per_M": 3.00,
                "claude_sonnet_output_per_M": 15.00,
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
    lines.append(f"Run date: {datetime.now().strftime('%Y-%m-%d')}\n")
    lines.append("## Summary Table\n")

    # Header
    lines.append("| Framework | LoC | CC | Avg Tokens (In/Out) | Avg Step Eff | Avg Latency (s) | Avg Correct | Avg Cost ($) | Avg pass³ |")
    lines.append("|-----------|-----|----|--------------------|--------------|-----------------|-------------|--------------|-----------|")

    # Rows
    for fw_name, fw_results in all_results.items():
        if fw_results.get("status") == "not_implemented":
            lines.append(f"| {fw_name} | - | - | - | - | - | - | - | - |")
            continue

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
        avg_step_eff = sum(s["median_step_efficiency"] for s in scenarios.values()) / len(scenarios)

        # Average correctness
        all_correctness = []
        for s in scenarios.values():
            all_correctness.extend(s["per_run_correctness"])
        avg_correct = sum(all_correctness) / len(all_correctness) if all_correctness else 0

        lines.append(
            f"| {fw_name} | {loc} | {cc:.1f} | {int(avg_input)}/{int(avg_output)} | "
            f"{avg_step_eff:.2f} | {avg_latency:.2f} | {avg_correct:.2f} | {avg_cost:.4f} | {avg_pass3:.2f} |"
        )

    # Detailed section
    lines.append("\n## Detailed Results by Scenario\n")
    for fw_name, fw_results in all_results.items():
        if fw_results.get("status") == "not_implemented":
            continue

        lines.append(f"\n### {fw_name}\n")
        scenarios = fw_results.get("scenarios", {})

        for sid, sdata in scenarios.items():
            lines.append(f"\n**{sid}:**")
            lines.append(f"- Median latency: {sdata['median_latency']}s")
            lines.append(f"- Median tokens: {sdata['median_input_tokens']} in / {sdata['median_output_tokens']} out")
            lines.append(f"- Median cost: ${sdata['median_cost_usd']}")
            lines.append(f"- Median step efficiency: {sdata['median_step_efficiency']}")
            lines.append(f"- Consistency (pass³): {sdata['consistency_pass3']}")
            lines.append(f"- Per-run correctness: {sdata['per_run_correctness']}")

    with open("arena/results/results_table.md", "w") as f:
        f.write("\n".join(lines))

    print("✓ Generated: arena/results/results_table.md")


def main():
    """Run benchmark with CLI options."""
    parser = argparse.ArgumentParser(
        description="Arena: Agent Framework Comparison Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python -m arena.runner_simple                          # full benchmark
  python -m arena.runner_simple --frameworks aws_strands crewai
  python -m arena.runner_simple --scenarios T1 T4
  python -m arena.runner_simple --quick                  # K=1, T1 only
  python -m arena.runner_simple --reps 5                 # 5 repetitions
""")
    parser.add_argument(
        "--frameworks", nargs="+", choices=list(FRAMEWORKS.keys()),
        default=list(FRAMEWORKS.keys()),
        help="Frameworks to benchmark (default: all)")
    parser.add_argument(
        "--scenarios", nargs="+", choices=ALL_SCENARIOS,
        default=ALL_SCENARIOS,
        help="Scenarios to run (default: T1 T4 T5)")
    parser.add_argument(
        "--reps", type=int, default=DEFAULT_K,
        help=f"Repetitions per scenario (default: {DEFAULT_K})")
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick validation: K=1, T1 only")

    args = parser.parse_args()

    if args.quick:
        args.scenarios = ["T1"]
        args.reps = 1

    total_runs = len(args.frameworks) * len(args.scenarios) * args.reps
    print("\n" + "="*70)
    print("ARENA: Agent Framework Comparison Benchmark")
    print("="*70)
    print(f"  Frameworks: {', '.join(args.frameworks)}")
    print(f"  Scenarios:  {', '.join(args.scenarios)}")
    print(f"  Reps (K):   {args.reps}")
    print(f"  Total runs: {total_runs}")
    print("="*70)

    all_results = {}

    for fw_name in args.frameworks:
        try:
            results = run_framework_benchmark(fw_name, args.scenarios, args.reps)
            all_results[fw_name] = results
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\nFramework {fw_name} failed: {e}")
            all_results[fw_name] = {"error": str(e)}

    # Generate outputs
    generate_results_json(all_results)
    generate_results_table(all_results)

    print("\n" + "="*70)
    print("Benchmark complete!")
    print(f"  Results: arena/results/results.json")
    print(f"  Table:   arena/results/results_table.md")
    print("="*70)


if __name__ == "__main__":
    main()
