#!/usr/bin/env python3
"""
Run Scenario-2 (Complex Multi-Issue) Benchmark - Iteration Runner

Usage:
    python scripts/run_scenario2.py 1    # Run iteration 1
    python scripts/run_scenario2.py 2    # Run iteration 2
"""
import sys
from pathlib import Path
import json
from datetime import datetime
from statistics import median
import time
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_scenario2_iteration(iteration_number: int):
    """Run a complete Scenario-2 benchmark iteration and save results."""

    print(f"\n{'='*80}")
    print(f"SCENARIO-2 ITERATION {iteration_number}")
    print(f"Complex Multi-Issue Customer Support (S2)")
    print(f"{'='*80}\n")

    # Import after printing banner
    from arena.scenarios import SYSTEM_PROMPT, SCENARIOS
    from arena.frameworks.aws_strands_agent import AWSStrandsAdapter
    from arena.frameworks.google_adk_agent import GoogleADKAdapter
    from arena.frameworks.crewai_agent import CrewAIAdapter
    from arena.frameworks.claude_sdk_agent import ClaudeSDKAdapter
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
        },
        "aws_strands": {
            "adapter": AWSStrandsAdapter,
            "file": "arena/frameworks/aws_strands_agent.py",
        },
        "google_adk": {
            "adapter": GoogleADKAdapter,
            "file": "arena/frameworks/google_adk_agent.py",
        },
        "crewai": {
            "adapter": CrewAIAdapter,
            "file": "arena/frameworks/crewai_agent.py",
        },
    }

    K = 3  # repetitions per scenario

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

        correctness_result = evaluate_scenario(scenario_id, tool_log, final_response)
        step_eff_result = compute_step_efficiency(scenario_id, tool_log)
        cost = compute_cost(usage["input_tokens"], usage["output_tokens"])

        return {
            "latency": latency,
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "correctness": correctness_result["correctness_score"],
            "step_efficiency": step_eff_result["step_efficiency_ratio"],
            "cost_usd": cost,
            "tool_count": len(tool_log),
        }

    def run_framework_benchmark(fw_name: str):
        """Run S2 benchmark for one framework."""
        print(f"\n{'='*70}")
        print(f"BENCHMARKING: {fw_name}")
        print(f"{'='*70}")

        fw_data = FRAMEWORKS[fw_name]
        adapter_class = fw_data["adapter"]
        file_path = fw_data["file"]

        # Measure code complexity
        complexity_result = measure_code_complexity(file_path)

        results = {
            "lines_of_code": complexity_result["lines_of_code"],
            "cyclomatic_complexity": complexity_result["cyclomatic_complexity"],
            "scenarios": {}
        }

        # Only run S2 for Scenario-2
        scenario_id = "S2"
        print(f"\n--- Test {scenario_id} ---")
        runs = []

        for rep in range(1, K + 1):
            try:
                run_result = run_single_scenario(adapter_class, scenario_id)
                runs.append(run_result)
                print(f"  Rep {rep}/{K}... ✓ (correctness: {run_result['correctness']:.2f})")
            except Exception as e:
                print(f"  Rep {rep}/{K}... ✗ Error: {str(e)[:50]}")
                import traceback
                traceback.print_exc()
                continue

        if not runs:
            print(f"  All repetitions failed for {scenario_id}")
            return results

        # Compute medians
        latencies = [r["latency"] for r in runs]
        input_tokens = [r["input_tokens"] for r in runs]
        output_tokens = [r["output_tokens"] for r in runs]
        costs = [r["cost_usd"] for r in runs]
        step_effs = [r["step_efficiency"] for r in runs]
        correctnesses = [r["correctness"] for r in runs]

        consistency_result = compute_consistency(correctnesses)

        results["scenarios"][scenario_id] = {
            "median_latency": round(median(latencies), 2),
            "median_input_tokens": int(median(input_tokens)),
            "median_output_tokens": int(median(output_tokens)),
            "median_cost_usd": round(median(costs), 4),
            "median_step_efficiency": round(median(step_effs), 2),
            "consistency_pass3": consistency_result["consistency_pass3"],
            "per_run_correctness": [round(c, 2) for c in correctnesses],
        }

        return results

    # Run all frameworks in randomized order
    all_results = {}

    # Randomize framework testing order to eliminate cache bias
    framework_names = list(FRAMEWORKS.keys())
    random.shuffle(framework_names)

    print(f"\n{'='*80}")
    print(f"RANDOMIZED TESTING ORDER:")
    for i, fw_name in enumerate(framework_names, 1):
        print(f"  {i}. {fw_name}")
    print(f"{'='*80}\n")

    for fw_name in framework_names:
        try:
            results = run_framework_benchmark(fw_name)
            all_results[fw_name] = results
        except Exception as e:
            print(f"\n✗ Framework {fw_name} failed: {e}")
            import traceback
            traceback.print_exc()
            all_results[fw_name] = {"error": str(e)}

    # Create iteration directory
    iteration_dir = Path(__file__).parent.parent / "scenarios" / "scenario-2" / "iterations" / f"iteration-{iteration_number}"
    results_dir = iteration_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save combined results
    combined_results = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "iteration": iteration_number,
        "scenario_type": "complex_multi_issue",
        "testing_order": framework_names,  # Record randomized order
        "model_config": {
            "claude_model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "temperature": 0,
            "aws_profile": "prod-tools",
            "pricing": {
                "claude_sonnet_input_per_M": 3.0,
                "claude_sonnet_output_per_M": 15.0
            }
        },
        "frameworks": all_results
    }

    # Save results
    results_file = results_dir / "combined_results.json"
    with open(results_file, "w") as f:
        json.dump(combined_results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"SCENARIO-2 ITERATION {iteration_number} COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: {results_file}")

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY - S2: The Frustrated Premium Customer")
    print(f"{'='*80}\n")

    for fw_name, fw_results in all_results.items():
        if "error" in fw_results:
            print(f"{fw_name}: ERROR - {fw_results['error']}")
            continue

        print(f"{fw_name}:")
        print(f"  LoC: {fw_results['lines_of_code']}, CC: {fw_results['cyclomatic_complexity']:.1f}")
        s4_data = fw_results.get("scenarios", {}).get("S2")
        if s4_data:
            print(f"  S2: latency={s4_data['median_latency']:.2f}s, "
                  f"correctness={s4_data['per_run_correctness']}, "
                  f"pass³={s4_data['consistency_pass3']:.2f}")
        print()

    # Generate summary
    generate_summary(iteration_number, combined_results, iteration_dir)

    return combined_results


def generate_summary(iteration: int, results: dict, iteration_dir: Path):
    """Generate a summary markdown file for the iteration."""
    summary_file = iteration_dir / f"ITERATION_{iteration}_SUMMARY.md"

    frameworks = results.get("frameworks", {})

    # Calculate average metrics
    framework_stats = {}
    for fw_name, fw_data in frameworks.items():
        if "error" in fw_data:
            continue

        scenarios = fw_data.get("scenarios", {})
        s4 = scenarios.get("S2", {})

        if not s4:
            continue

        per_run = s4.get("per_run_correctness", [])
        avg_correctness = sum(per_run) / len(per_run) if per_run else 0

        framework_stats[fw_name] = {
            "latency": s4.get("median_latency", 0),
            "correctness": avg_correctness,
            "consistency": s4.get("consistency_pass3", 0),
            "tokens_in": s4.get("median_input_tokens", 0),
            "tokens_out": s4.get("median_output_tokens", 0),
            "cost": s4.get("median_cost_usd", 0),
            "step_efficiency": s4.get("median_step_efficiency", 0),
        }

    # Sort by latency
    sorted_frameworks = sorted(framework_stats.items(), key=lambda x: x[1]["latency"])

    # Generate markdown
    summary = [
        f"# Scenario-2 Iteration {iteration} - Results Summary",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d')}",
        f"**Status**: ✅ Complete",
        f"**Scenario**: S2 - The Frustrated Premium Customer (Complex Multi-Issue)",
        "",
        "---",
        "",
        "## Quick Results",
        "",
    ]

    if sorted_frameworks:
        winner = sorted_frameworks[0]
        summary.extend([
            f"### Overall Winner: 🥇 {winner[0].replace('_', ' ').title()}",
            f"- **Latency**: {winner[1]['latency']:.2f}s",
            f"- **Correctness**: {winner[1]['correctness']*100:.2f}%",
            f"- **Consistency**: {winner[1]['consistency']*100:.0f}%",
            "",
        ])

    summary.extend([
        "### Complete Rankings (by Latency)",
        "",
    ])

    medals = ["🥇", "🥈", "🥉", ""]
    for i, (fw_name, stats) in enumerate(sorted_frameworks):
        medal = medals[i] if i < 3 else f"{i+1}."
        fw_display = fw_name.replace("_", " ").title()
        summary.append(
            f"{medal} **{fw_display}** - {stats['latency']:.2f}s, "
            f"{stats['correctness']*100:.2f}% correctness, "
            f"{stats['consistency']*100:.0f}% pass³"
        )

    summary.extend([
        "",
        "---",
        "",
        "## Detailed Results",
        "",
        "### S2: The Frustrated Premium Customer",
        "",
        "**Customer Issues**:",
        "1. Damaged laptop #ORD-1234 (needs refund)",
        "2. Wrong headphones #ORD-5678 (needs cancellation)",
        "3. Address change for USB hub #ORD-9012 (in transit)",
        "",
        "| Framework | Latency | Tokens (In/Out) | Cost | Correctness | Pass³ | Step Eff |",
        "|-----------|---------|-----------------|------|-------------|-------|----------|",
    ])

    for fw_name, stats in sorted_frameworks:
        fw_display = fw_name.replace("_", " ").title()
        tokens_display = f"{stats['tokens_in']}/{stats['tokens_out']}" if stats['tokens_in'] > 0 else "0*/0*"
        cost_display = f"${stats['cost']:.4f}" if stats['cost'] > 0 else "$0.00*"
        correctness_display = f"{stats['correctness']*100:.2f}%"
        pass3_display = "✅ 1.00" if stats['consistency'] >= 1.0 else f"⚠️ {stats['consistency']:.2f}"
        step_eff_display = f"{stats['step_efficiency']:.2f}"

        summary.append(
            f"| {fw_display} | {stats['latency']:.2f}s | {tokens_display} | {cost_display} | "
            f"{correctness_display} | {pass3_display} | {step_eff_display} |"
        )

    summary.extend([
        "",
        "*Note: 0* indicates token tracking not available for this framework",
        "",
        "---",
        "",
        f"**Iteration {iteration} Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Scenario**: Complex Multi-Issue Support",
        f"**Frameworks Tested**: {len(framework_stats)}",
        f"**Total Runs**: {len(framework_stats) * 3} (K=3)",
        "",
    ])

    with open(summary_file, "w") as f:
        f.write("\n".join(summary))

    print(f"✅ Summary saved to: {summary_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_scenario2.py <iteration_number>")
        print("Example: python scripts/run_scenario2.py 1")
        sys.exit(1)

    try:
        iteration_num = int(sys.argv[1])
        if iteration_num < 1:
            raise ValueError("Iteration number must be positive")
    except ValueError as e:
        print(f"Error: Invalid iteration number - {e}")
        sys.exit(1)

    run_scenario2_iteration(iteration_num)
