"""Test scenarios for Arena benchmark."""

# System prompt (same for all 6 frameworks)
SYSTEM_PROMPT = """You are a customer support agent for TechCorp,
an online electronics retailer.

Help customers with their inquiries using the available tools.
Guidelines:
1. Always look up the customer's profile first.
2. For order-related issues, retrieve the customer's orders.
3. For general questions, search the knowledge base.
4. Process refunds when the customer has a valid reason and
   the order is eligible.
5. Escalate to a human agent for billing disputes or issues
   you cannot resolve.
6. Be helpful, empathetic, and concise."""

# Test scenarios
# S1/S1b/S1c = Simple single-issue tests (Scenario-1 directory)
# S2 = Complex multi-issue test (Scenario-2 directory)
# S3 = Multi-agent product investigation (Scenario-3 directory)
SCENARIOS = {
    "S1": {
        "customer_id": "CUST-001",
        "user_message": "Hi, this is customer CUST-001. I ordered a laptop 3 days ago and it arrived damaged. Order #ORD-1234. I want a refund.",
        "expected_tools": ["get_customer", "get_orders", "process_refund"],
        "optimal_steps": 3,
        "correctness_criteria": {
            "looked_up_customer": "get_customer in tool_log",
            "retrieved_orders": "get_orders in tool_log",
            "processed_refund": "process_refund in tool_log",
            "confirmed_to_customer": 'any(kw in final_response.lower() for kw in ["1299", "1,299", "refund"])',
        }
    },
    "S1b": {
        "customer_id": "CUST-001",
        "user_message": "Hi, I'm customer CUST-001. How do I change my shipping address for an upcoming delivery?",
        "expected_tools": ["get_customer", "get_orders", "search_knowledge_base"],
        "optimal_steps": 3,
        "correctness_criteria": {
            "looked_up_customer": "get_customer in tool_log",
            "retrieved_orders": "get_orders in tool_log",
            "searched_kb": "search_knowledge_base in tool_log",
            "provided_instructions": '"account settings" in final_response.lower() or "addresses" in final_response.lower()',
            # Negative criteria: should NOT process refund or escalate
            "did_not_refund": "process_refund not in tool_log",
            "did_not_escalate": "escalate_to_human not in tool_log",
        }
    },
    "S1c": {
        "customer_id": "CUST-001",
        "user_message": "Hello, this is customer CUST-001. I was charged twice for my last order #ORD-5678. Can you help?",
        "expected_tools": ["get_customer", "get_orders", "search_knowledge_base", "escalate_to_human"],
        "optimal_steps": 4,
        "correctness_criteria": {
            "looked_up_order": "get_orders in tool_log",
            "searched_kb": "search_knowledge_base in tool_log",
            "escalated_to_human": "escalate_to_human in tool_log",
            "provided_confirmation": '"esc" in final_response.lower() or "human" in final_response.lower() or "agent" in final_response.lower()',
        }
    },
    # Scenario-2: Complex Multi-Issue
    "S2": {
        "customer_id": "CUST-001",
        "user_message": """Hi, this is customer CUST-001. I'm really frustrated. I have THREE issues:

1. My laptop order #ORD-1234 from 3 days ago arrived damaged
2. I have headphones #ORD-5678 processing, but I want to cancel it - I ordered the wrong model
3. My shipping address changed and I need to update it for the USB hub #ORD-9012 that's already shipped

Can you help me sort all this out?""",
        "expected_tools": ["get_customer", "get_orders", "process_refund", "search_knowledge_base", "escalate_to_human"],
        "optimal_steps": 8,  # More complex, multi-issue scenario
        "correctness_criteria": {
            # Core Actions (62.5% total)
            "looked_up_customer": "get_customer in tool_log",
            "retrieved_all_orders": "get_orders in tool_log",
            "handled_damaged_laptop": "process_refund in tool_log and 'ORD-1234' in str(tool_log)",
            "addressed_cancellation": "('search_knowledge_base' in tool_log or 'escalate_to_human' in tool_log) and ('5678' in final_response or '5678' in str(tool_log))",
            "addressed_address_change": "'search_knowledge_base' in tool_log",
            # Response Quality (37.5% total)
            "acknowledged_all_issues": "(('laptop' in final_response.lower() or '1234' in final_response) and ('headphones' in final_response.lower() or '5678' in final_response) and ('hub' in final_response.lower() or '9012' in final_response))",
            "correct_order_handling": "'5678' not in str([call for call in tool_log if 'process_refund' in str(call)]) and '9012' not in str([call for call in tool_log if 'process_refund' in str(call)])",
            "premium_acknowledgement": "'premium' in final_response.lower() or 'expedited' in final_response.lower()",
        }
    },
    # Scenario-3: Multi-Agent Product Investigation & Recommendation
    "S3": {
        "customer_id": "CUST-001",
        "user_message": """Hi, this is customer CUST-001. I'm looking to upgrade my home office setup.
I recently had issues with my laptop #ORD-1234, and I'm wondering:

1. What's the status of my refund?
2. Can you recommend a better laptop model based on my purchase history?
3. I also need a good monitor and keyboard to go with it
4. What's my total spending this year and do I qualify for any discounts?

I want reliable products and I'm willing to spend up to $3000 total.
Can you help me put together a complete setup?""",
        "expected_tools": ["get_customer", "get_orders", "search_knowledge_base", "get_product_catalog", "calculate_discount"],
        "optimal_steps": 12,  # Multi-agent collaboration scenario
        "correctness_criteria": {
            # Research Phase (30%)
            "looked_up_customer": "get_customer in tool_log",
            "retrieved_orders": "get_orders in tool_log",
            "searched_refund_info": "'search_knowledge_base' in tool_log and any('refund' in str(call).lower() for call in tool_log)",
            "searched_products": "'search_knowledge_base' in tool_log and any('laptop' in str(call).lower() or 'product' in str(call).lower() for call in tool_log)",
            "used_catalog": "'get_product_catalog' in tool_log",
            # Analysis Phase (25%)
            "confirmed_refund_status": "'1234' in final_response and ('refund' in final_response.lower() or 'processing' in final_response.lower())",
            "calculated_spending": "'get_customer' in tool_log or 'spending' in final_response.lower() or '8450' in final_response",
            "checked_discounts": "'calculate_discount' in tool_log or ('discount' in final_response.lower() and 'premium' in final_response.lower())",
            # Communication Phase (25%)
            "addressed_all_questions": "(('refund' in final_response.lower() or '1234' in final_response) and ('laptop' in final_response.lower() or 'recommend' in final_response.lower()) and ('monitor' in final_response.lower() or 'keyboard' in final_response.lower()) and ('discount' in final_response.lower() or 'spending' in final_response.lower()))",
            "provided_recommendations": "('techpro' in final_response.lower() or 'probook' in final_response.lower() or 'LAP-' in final_response) or ('ultraview' in final_response.lower() or 'prodisplay' in final_response.lower() or 'MON-' in final_response)",
            "within_budget": "'3000' in final_response or '2999' in final_response or '2899' in final_response or '2799' in final_response",
            # Multi-Agent Coordination (20%)
            "efficient_tool_usage": "len([c for c in tool_log if 'get_orders' in c]) <= 2",  # Avoid redundant calls
            "logical_sequence": "tool_log.index('get_customer') < (tool_log.index('get_product_catalog') if 'get_product_catalog' in tool_log else 999)",
        }
    }
}
