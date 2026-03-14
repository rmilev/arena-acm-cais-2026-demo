"""Run a complete benchmark iteration."""
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_iteration(iteration_number: int):
    """Run a complete benchmark iteration and save results."""

    print(f"\n{'='*80}")
    print(f"STARTING ITERATION {iteration_number}")
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
    from statistics import median
    import time

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
        """Run full benchmark for one framework."""
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

        for scenario_id in ["S1", "S1b", "S1c"]:
            print(f"\n--- Scenario {scenario_id} ---")
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
                continue

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

    # Run all frameworks
    all_results = {}

    for fw_name in FRAMEWORKS.keys():
        try:
            results = run_framework_benchmark(fw_name)
            all_results[fw_name] = results
        except Exception as e:
            print(f"\n✗ Framework {fw_name} failed: {e}")
            import traceback
            traceback.print_exc()
            all_results[fw_name] = {"error": str(e)}

    # Create iteration directory if it doesn't exist
    iteration_dir = Path(f"iterations/iteration-{iteration_number}")
    results_dir = iteration_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save combined results
    combined_results = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "iteration": iteration_number,
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
    with open(results_dir / "combined_results.json", "w") as f:
        json.dump(combined_results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"ITERATION {iteration_number} COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: {results_dir}/")
    print(f"  - combined_results.json")

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    for fw_name, fw_results in all_results.items():
        if "error" in fw_results:
            print(f"{fw_name}: ERROR - {fw_results['error']}")
            continue

        print(f"{fw_name}:")
        print(f"  LoC: {fw_results['lines_of_code']}, CC: {fw_results['cyclomatic_complexity']:.1f}")
        for sid, sdata in fw_results.get("scenarios", {}).items():
            print(f"  {sid}: latency={sdata['median_latency']:.2f}s, "
                  f"correctness={sdata['per_run_correctness']}, "
                  f"pass³={sdata['consistency_pass3']:.2f}")
        print()

    return combined_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_iteration.py <iteration_number>")
        sys.exit(1)

    iteration_num = int(sys.argv[1])
    run_iteration(iteration_num)
