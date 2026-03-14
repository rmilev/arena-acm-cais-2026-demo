#!/usr/bin/env python3
"""Arena MCP Server V2 - Extended with 8 tools for multi-agent scenario."""
from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("arena-support-tools-v2")

# --- Tool call tracking (for Metric 3) ---
_tool_call_log: list[str] = []


@mcp.tool()
def get_customer(customer_id: str) -> str:
    """Look up a customer profile by ID."""
    _tool_call_log.append("get_customer")
    if customer_id == "CUST-001":
        return json.dumps({
            "id": "CUST-001",
            "name": "Jane Smith",
            "email": "jane.smith@email.com",
            "phone": "+1-555-0123",
            "tier": "premium",
            "account_since": "2023-01-15",
            "lifetime_orders": 47,
            "ytd_spending": 8450.32
        })
    return json.dumps({"error": "Customer not found"})


@mcp.tool()
def get_orders(customer_id: str) -> str:
    """Retrieve all orders for a customer."""
    _tool_call_log.append("get_orders")
    if customer_id == "CUST-001":
        return json.dumps([
            {
                "order_id": "ORD-1234",
                "product": "ProBook Laptop 15-inch",
                "amount": 1299.99,
                "status": "delivered",
                "order_date": "2026-03-09",
                "delivery_date": "2026-03-11",
                "refund_eligible": True,
                "refund_status": "processing",
                "refund_amount": 1299.99,
                "issue": "Damaged on arrival - screen cracked"
            },
            {
                "order_id": "ORD-5678",
                "product": "NoiseCancel Pro Headphones",
                "amount": 199.99,
                "status": "processing",
                "order_date": "2026-03-10",
                "delivery_date": None,
                "refund_eligible": False,
                "note": "Two charges of $199.99 recorded"
            },
            {
                "order_id": "ORD-9012",
                "product": "USB-C Hub 7-in-1",
                "amount": 49.99,
                "status": "shipped",
                "order_date": "2026-03-11",
                "delivery_date": None,
                "refund_eligible": False
            }
        ])
    return json.dumps([])


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base."""
    _tool_call_log.append("search_knowledge_base")
    # Simple keyword matching against 8 articles (5 original + 3 new)
    articles = [
        {
            "id": "KB-001",
            "title": "Refund Policy",
            "keywords": ["refund", "return", "damaged", "defective"],
            "content": "Refunds are available within 30 days of delivery for damaged or defective items. Premium customers receive expedited processing (1-2 business days). Standard refunds take 3-5 business days. Refund status can be tracked in your order history."
        },
        {
            "id": "KB-002",
            "title": "How to Change Shipping Address",
            "keywords": ["shipping", "address", "change", "update", "delivery"],
            "content": "To change your shipping address: 1) Go to Account Settings > Addresses. 2) Click Edit on the address. 3) For in-transit orders, contact support within 24 hours of shipment. Changes cannot be made once the package is out for delivery."
        },
        {
            "id": "KB-003",
            "title": "Billing Disputes",
            "keywords": ["billing", "charge", "charged", "twice", "double", "dispute", "overcharged"],
            "content": "Billing disputes require manual review by our finance team. Please escalate to a human agent who will initiate the investigation. Typical resolution: 5-7 business days. If confirmed, a full refund is issued."
        },
        {
            "id": "KB-004",
            "title": "Order Tracking",
            "keywords": ["track", "tracking", "where", "status", "delivery"],
            "content": "Track your order in Account > Orders. Status updates: processing, shipped, out for delivery, delivered."
        },
        {
            "id": "KB-005",
            "title": "Premium Membership Benefits",
            "keywords": ["premium", "membership", "benefits", "tier", "discount"],
            "content": "Premium members get: 10% discount on orders over $500, free expedited shipping, priority support, early access to new products, and extended return windows (45 days vs 30 days)."
        },
        {
            "id": "KB-006",
            "title": "Laptop Buying Guide",
            "keywords": ["laptop", "computer", "recommend", "recommendation", "upgrade"],
            "content": "Top laptops 2026: TechPro Elite 16 ($1899) - best for power users, ProBook Ultra 15 ($1599) - balanced performance, BudgetBook Air ($899) - best value. Consider RAM (16GB min), SSD (512GB min), and warranty coverage."
        },
        {
            "id": "KB-007",
            "title": "Monitor & Accessory Recommendations",
            "keywords": ["monitor", "keyboard", "mouse", "accessories", "peripheral"],
            "content": "Recommended monitors: UltraView 4K 27-inch ($599), ProDisplay 32-inch ($799). Keyboards: MechPro RGB ($149), SilentType Pro ($89). Mice: PrecisionClick ($69), ErgoMouse ($49). Bundle discounts available."
        },
        {
            "id": "KB-008",
            "title": "How to Order Products",
            "keywords": ["order", "buy", "purchase", "checkout", "cart"],
            "content": "To place an order: 1) Browse products or use search. 2) Add items to cart. 3) Review cart and apply discount codes. 4) Proceed to checkout. 5) Confirm shipping address and payment. Orders typically ship within 1-2 business days."
        }
    ]

    query_lower = query.lower()
    matches = []
    for article in articles:
        if any(kw in query_lower for kw in article["keywords"]):
            matches.append(article)

    if matches:
        return json.dumps(matches)
    return json.dumps({"message": "No matching articles found", "suggestion": "Try different keywords or contact support"})


@mcp.tool()
def process_refund(order_id: str, reason: str) -> str:
    """Process a refund for an order."""
    _tool_call_log.append("process_refund")
    # Simulate refund processing
    if order_id == "ORD-1234":
        return json.dumps({
            "status": "success",
            "refund_id": "REF-8901",
            "order_id": order_id,
            "amount": 1299.99,
            "reason": reason,
            "processing_time": "1-2 business days (premium customer)",
            "message": "Refund has been initiated. You will receive confirmation via email."
        })
    elif order_id in ["ORD-5678", "ORD-9012"]:
        return json.dumps({
            "status": "error",
            "message": f"Order {order_id} is not eligible for refund. Current status does not allow refund processing."
        })
    return json.dumps({"status": "error", "message": "Order not found"})


@mcp.tool()
def escalate_to_human(issue_summary: str, customer_id: str) -> str:
    """Escalate an issue to a human support agent."""
    _tool_call_log.append("escalate_to_human")
    return json.dumps({
        "status": "escalated",
        "ticket_id": "TICKET-5567",
        "customer_id": customer_id,
        "issue": issue_summary,
        "assigned_to": "Senior Support Team",
        "estimated_response": "1-2 hours",
        "message": "Your issue has been escalated to our senior support team. You will be contacted shortly."
    })


# --- NEW TOOLS FOR SCENARIO-3 (Multi-Agent) ---

@mcp.tool()
def get_product_catalog(category: str) -> str:
    """Get product catalog for a category (laptops, monitors, keyboards, bundles)."""
    _tool_call_log.append("get_product_catalog")

    catalogs = {
        "laptops": [
            {
                "product_id": "LAP-001",
                "name": "TechPro Elite 16",
                "price": 1899.00,
                "specs": "Intel i9, 32GB RAM, 1TB SSD, RTX 4070",
                "rating": 4.8,
                "stock": "in_stock",
                "warranty": "3 years"
            },
            {
                "product_id": "LAP-002",
                "name": "ProBook Ultra 15",
                "price": 1599.00,
                "specs": "Intel i7, 16GB RAM, 512GB SSD, RTX 4060",
                "rating": 4.6,
                "stock": "in_stock",
                "warranty": "2 years"
            },
            {
                "product_id": "LAP-003",
                "name": "BudgetBook Air 14",
                "price": 899.00,
                "specs": "Intel i5, 8GB RAM, 256GB SSD, Integrated Graphics",
                "rating": 4.3,
                "stock": "low_stock",
                "warranty": "1 year"
            }
        ],
        "monitors": [
            {
                "product_id": "MON-001",
                "name": "UltraView 4K 27-inch",
                "price": 599.00,
                "specs": "4K 60Hz, IPS, HDR400",
                "rating": 4.7,
                "stock": "in_stock"
            },
            {
                "product_id": "MON-002",
                "name": "ProDisplay 32-inch",
                "price": 799.00,
                "specs": "4K 75Hz, IPS, HDR600, USB-C",
                "rating": 4.9,
                "stock": "in_stock"
            }
        ],
        "keyboards": [
            {
                "product_id": "KEY-001",
                "name": "MechPro RGB",
                "price": 149.00,
                "specs": "Mechanical, Cherry MX Brown, RGB",
                "rating": 4.8,
                "stock": "in_stock"
            },
            {
                "product_id": "KEY-002",
                "name": "SilentType Pro",
                "price": 89.00,
                "specs": "Membrane, Quiet, Wireless",
                "rating": 4.5,
                "stock": "in_stock"
            }
        ],
        "bundles": [
            {
                "bundle_id": "BUN-001",
                "name": "Power User Bundle",
                "products": ["LAP-001", "MON-002", "KEY-001"],
                "price": 2799.00,
                "savings": 148.00,
                "description": "TechPro Elite + ProDisplay + MechPro"
            },
            {
                "bundle_id": "BUN-002",
                "name": "Professional Bundle",
                "products": ["LAP-002", "MON-001", "KEY-002"],
                "price": 2299.00,
                "savings": 88.00,
                "description": "ProBook Ultra + UltraView + SilentType"
            }
        ]
    }

    category_lower = category.lower()
    if category_lower in catalogs:
        return json.dumps({
            "category": category,
            "products": catalogs[category_lower],
            "count": len(catalogs[category_lower])
        })

    return json.dumps({
        "error": f"Category '{category}' not found",
        "available_categories": list(catalogs.keys())
    })


@mcp.tool()
def calculate_discount(customer_id: str, total_amount: float) -> str:
    """Calculate applicable discounts for a customer based on tier and spending."""
    _tool_call_log.append("calculate_discount")

    if customer_id == "CUST-001":
        # Premium customer with $8450 YTD spending
        discounts = []
        total_discount = 0.0

        # Premium tier discount (10% on orders > $500)
        if total_amount > 500:
            premium_discount = total_amount * 0.10
            discounts.append({
                "type": "premium_tier",
                "name": "Premium Member 10% Discount",
                "amount": round(premium_discount, 2)
            })
            total_discount += premium_discount

        # High spender bonus (YTD > $5000 gets additional 5%)
        if total_amount > 1000:  # Only on large purchases
            loyalty_discount = total_amount * 0.05
            discounts.append({
                "type": "loyalty_bonus",
                "name": "Loyal Customer 5% Bonus",
                "amount": round(loyalty_discount, 2)
            })
            total_discount += loyalty_discount

        return json.dumps({
            "customer_id": customer_id,
            "original_amount": total_amount,
            "discounts": discounts,
            "total_discount": round(total_discount, 2),
            "final_amount": round(total_amount - total_discount, 2),
            "savings_percent": round((total_discount / total_amount) * 100, 1) if total_amount > 0 else 0
        })

    return json.dumps({
        "customer_id": customer_id,
        "original_amount": total_amount,
        "discounts": [],
        "total_discount": 0.0,
        "final_amount": total_amount,
        "message": "No discounts available for this customer"
    })


@mcp.tool()
def check_inventory(product_id: str) -> str:
    """Check product availability and estimated delivery."""
    _tool_call_log.append("check_inventory")

    inventory = {
        "LAP-001": {"stock": 47, "status": "in_stock", "delivery": "1-2 business days"},
        "LAP-002": {"stock": 32, "status": "in_stock", "delivery": "1-2 business days"},
        "LAP-003": {"stock": 8, "status": "low_stock", "delivery": "2-3 business days"},
        "MON-001": {"stock": 156, "status": "in_stock", "delivery": "1-2 business days"},
        "MON-002": {"stock": 89, "status": "in_stock", "delivery": "1-2 business days"},
        "KEY-001": {"stock": 203, "status": "in_stock", "delivery": "1-2 business days"},
        "KEY-002": {"stock": 145, "status": "in_stock", "delivery": "1-2 business days"}
    }

    if product_id in inventory:
        return json.dumps({
            "product_id": product_id,
            **inventory[product_id]
        })

    return json.dumps({
        "product_id": product_id,
        "status": "not_found",
        "message": "Product ID not found in inventory"
    })


# --- Admin tools (used by adapters to inspect/reset tool call log) ---

@mcp.tool()
def arena_get_log() -> str:
    """Return the tool call log as JSON."""
    import json
    return json.dumps(_tool_call_log.copy())


@mcp.tool()
def arena_reset_log() -> str:
    """Reset the tool call log."""
    _tool_call_log.clear()
    return "Log reset"


# Keep utility functions for backward compat with multiagent adapters
def get_tool_log() -> list[str]:
    """Return the tool call log (for testing)."""
    return _tool_call_log.copy()


def reset_tool_log() -> None:
    """Reset the tool call log."""
    _tool_call_log.clear()


if __name__ == "__main__":
    mcp.run()
