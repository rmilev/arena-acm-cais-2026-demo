"""Metrics helpers for Arena benchmark.

6 metrics:
  1. LoC + Cyclomatic Complexity  (code complexity)
  2. Step Efficiency Ratio        (reasoning quality)
  3. Wall-Clock Latency           (user experience)
  4. Correctness                  (ground truth — see evaluator.py)
  5. Consistency (pass^3)         (reliability)
  6. Cost per Task ($)            (operational expense — from token counts)
"""
from radon.complexity import cc_visit


# ---------------------------------------------------------------------------
# Metric 1: Lines of Code + Cyclomatic Complexity
# ---------------------------------------------------------------------------
def measure_code_complexity(filepath: str) -> dict:
    """Measure LoC and Cyclomatic Complexity for a file."""
    with open(filepath) as f:
        source = f.read()

    # LoC: non-blank, non-comment lines
    loc = sum(
        1 for line in source.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )

    # CC: radon returns a list of complexity results per function/method
    cc_results = cc_visit(source)
    if cc_results:
        avg_cc = sum(r.complexity for r in cc_results) / len(cc_results)
    else:
        avg_cc = 1.0  # no functions = trivially simple

    return {
        "lines_of_code": loc,
        "cyclomatic_complexity": round(avg_cc, 1)
    }


# ---------------------------------------------------------------------------
# Metric 2: Step Efficiency Ratio
# ---------------------------------------------------------------------------
OPTIMAL_STEPS = {"S1": 3, "S1b": 3, "S1c": 4, "S2": 8, "S3": 12}


def compute_step_efficiency(scenario_id: str, tool_log: list[str]) -> dict:
    """Compute step efficiency ratio = actual_calls / optimal_calls."""
    actual = len(tool_log)
    optimal = OPTIMAL_STEPS.get(scenario_id, actual)  # fallback to actual if unknown
    ratio = round(actual / optimal, 1) if optimal > 0 else 0.0
    return {
        "tool_calls": tool_log,
        "num_tool_calls": actual,
        "optimal_tool_calls": optimal,
        "step_efficiency_ratio": ratio,
    }


# ---------------------------------------------------------------------------
# Metric 3: Wall-Clock Latency — measured in runner.py via time.perf_counter()
# ---------------------------------------------------------------------------
# No helper needed; latency_seconds is captured directly by the runner.


# ---------------------------------------------------------------------------
# Metric 4: Correctness — implemented in evaluator.py
# ---------------------------------------------------------------------------
# No helper needed here; see evaluator.py for per-scenario scoring.


# ---------------------------------------------------------------------------
# Metric 6: Cost per Task ($)
# ---------------------------------------------------------------------------
PRICING = {
    "claude_sonnet": {
        "input_per_M": 3.00,   # $/1M input tokens
        "output_per_M": 15.00,  # $/1M output tokens
    },
    "gemini_flash": {
        "input_per_M": 0.10,
        "output_per_M": 0.40,
    },
}


def compute_cost(input_tokens: int, output_tokens: int, model: str = "claude_sonnet") -> float:
    """Compute USD cost for a single run. Supplementary metric."""
    p = PRICING.get(model, PRICING["claude_sonnet"])
    cost = (input_tokens / 1_000_000) * p["input_per_M"] + \
           (output_tokens / 1_000_000) * p["output_per_M"]
    return round(cost, 4)


# ---------------------------------------------------------------------------
# Metric 5: Consistency (pass^3)
# ---------------------------------------------------------------------------
CONSISTENCY_THRESHOLD = 0.75  # minimum correctness to "pass"
K = 3  # number of repetitions


def compute_consistency(per_run_scores: list[float]) -> dict:
    """Compute pass^3 consistency.

    Returns 1.0 only if ALL k runs score >= threshold.
    A single failure drops consistency to 0.0.
    """
    if len(per_run_scores) < K:
        # Pad with 0.0 if fewer runs than expected (e.g., errors)
        per_run_scores = per_run_scores + [0.0] * (K - len(per_run_scores))
    all_passed = all(s >= CONSISTENCY_THRESHOLD for s in per_run_scores[:K])
    return {
        "per_run_correctness": per_run_scores[:K],
        "consistency_pass3": 1.0 if all_passed else 0.0,
    }
