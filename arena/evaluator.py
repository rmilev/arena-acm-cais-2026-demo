"""Correctness evaluator for Arena benchmark."""
from arena.scenarios import SCENARIOS


def evaluate_s1(tool_log: list[str], final_response: str) -> dict:
    """Score S1: Damaged Laptop Refund."""
    checks = {
        "looked_up_customer": "get_customer" in tool_log,
        "retrieved_orders": "get_orders" in tool_log,
        "processed_refund": "process_refund" in tool_log,
        "confirmed_to_customer": any(kw in final_response.lower() for kw in ["1299", "1,299", "refund"]),
    }
    score = sum(checks.values()) / len(checks)
    return {
        "correctness_score": round(score, 2),
        "correctness_details": checks,
    }


def evaluate_s1b(tool_log: list[str], final_response: str) -> dict:
    """Score S1b: Shipping Address Change."""
    checks = {
        "looked_up_customer": "get_customer" in tool_log,
        "retrieved_orders": "get_orders" in tool_log,
        "searched_kb": "search_knowledge_base" in tool_log,
        "provided_instructions": "account settings" in final_response.lower() or "addresses" in final_response.lower(),
        # Negative criteria
        "did_not_refund": "process_refund" not in tool_log,
        "did_not_escalate": "escalate_to_human" not in tool_log,
    }
    score = sum(checks.values()) / len(checks)
    return {
        "correctness_score": round(score, 2),
        "correctness_details": checks,
    }


def evaluate_s1c(tool_log: list[str], final_response: str) -> dict:
    """Score S1c: Double Charge / Billing Dispute."""
    checks = {
        "looked_up_order": "get_orders" in tool_log,
        "searched_kb": "search_knowledge_base" in tool_log,
        "escalated_to_human": "escalate_to_human" in tool_log,
        "provided_confirmation": any(kw in final_response.lower() for kw in ["esc", "human", "agent"]),
    }
    score = sum(checks.values()) / len(checks)
    return {
        "correctness_score": round(score, 2),
        "correctness_details": checks,
    }


def evaluate_s2(tool_log: list[str], final_response: str) -> dict:
    """Score S2: The Frustrated Premium Customer (Multi-Issue)."""
    tool_log_str = str(tool_log)
    final_response_lower = final_response.lower()

    # Check if refund was called with wrong order IDs
    refund_calls_str = str([call for call in tool_log if 'process_refund' in str(call)])

    checks = {
        # Core Actions (62.5% total)
        "looked_up_customer": "get_customer" in tool_log,
        "retrieved_all_orders": "get_orders" in tool_log,
        "handled_damaged_laptop": "process_refund" in tool_log and "1234" in tool_log_str,
        "addressed_cancellation": ("search_knowledge_base" in tool_log or "escalate_to_human" in tool_log) and ("5678" in final_response or "5678" in tool_log_str),
        "addressed_address_change": "search_knowledge_base" in tool_log,
        # Response Quality (37.5% total)
        "acknowledged_all_issues": (
            ("laptop" in final_response_lower or "1234" in final_response) and
            ("headphones" in final_response_lower or "5678" in final_response) and
            ("hub" in final_response_lower or "9012" in final_response)
        ),
        "correct_order_handling": "5678" not in refund_calls_str and "9012" not in refund_calls_str,
        "premium_acknowledgement": "premium" in final_response_lower or "expedited" in final_response_lower,
    }
    score = sum(checks.values()) / len(checks)
    return {
        "correctness_score": round(score, 2),
        "correctness_details": checks,
    }


def evaluate_s3(tool_log: list[str], final_response: str) -> dict:
    """Score S3: Multi-Agent Product Investigation & Recommendation."""
    tool_log_str = str(tool_log)
    final_response_lower = final_response.lower()

    checks = {
        # Research Phase (30%)
        "looked_up_customer": "get_customer" in tool_log,
        "retrieved_orders": "get_orders" in tool_log,
        "searched_refund_info": "search_knowledge_base" in tool_log and any("refund" in str(call).lower() for call in tool_log),
        "searched_products": "search_knowledge_base" in tool_log and any("laptop" in str(call).lower() or "product" in str(call).lower() for call in tool_log),
        "used_catalog": "get_product_catalog" in tool_log,
        # Analysis Phase (25%)
        "confirmed_refund_status": "1234" in final_response and ("refund" in final_response_lower or "processing" in final_response_lower),
        "calculated_spending": "get_customer" in tool_log or "spending" in final_response_lower or "8450" in final_response,
        "checked_discounts": "calculate_discount" in tool_log or ("discount" in final_response_lower and "premium" in final_response_lower),
        # Communication Phase (25%)
        "addressed_all_questions": (
            ("refund" in final_response_lower or "1234" in final_response) and
            ("laptop" in final_response_lower or "recommend" in final_response_lower) and
            ("monitor" in final_response_lower or "keyboard" in final_response_lower) and
            ("discount" in final_response_lower or "spending" in final_response_lower)
        ),
        "provided_recommendations": (
            ("techpro" in final_response_lower or "probook" in final_response_lower or "LAP-" in final_response) or
            ("ultraview" in final_response_lower or "prodisplay" in final_response_lower or "MON-" in final_response)
        ),
        "within_budget": "3000" in final_response or "2999" in final_response or "2899" in final_response or "2799" in final_response,
        # Multi-Agent Coordination (20%)
        "efficient_tool_usage": len([c for c in tool_log if "get_orders" in c]) <= 2,
        "logical_sequence": (
            "get_customer" in tool_log and "get_product_catalog" in tool_log and
            tool_log.index("get_customer") < tool_log.index("get_product_catalog")
        ) if ("get_customer" in tool_log and "get_product_catalog" in tool_log) else False,
    }
    score = sum(checks.values()) / len(checks)
    return {
        "correctness_score": round(score, 2),
        "correctness_details": checks,
    }


EVALUATORS = {
    "S1": evaluate_s1,
    "S1b": evaluate_s1b,
    "S1c": evaluate_s1c,
    "S2": evaluate_s2,
    "S3": evaluate_s3,
}


def evaluate_scenario(scenario_id: str, tool_log: list[str], final_response: str) -> dict:
    """Route to the appropriate evaluator.

    Returns dict with correctness_score (0.0-1.0) and correctness_details.
    """
    return EVALUATORS[scenario_id](tool_log, final_response)
