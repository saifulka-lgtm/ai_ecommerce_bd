"""
The single registry of all 15 AI tools: their provider-neutral specs (for
Claude/Ollama function calling, and for the mock provider's own reference)
and the actual callables that execute against the database. The agent never
calls a service or the database directly — only through here.
"""
from typing import Any, Callable, Dict

from app.ai.schemas import ToolSpec
from app.tools import product_tools, cart_tools, order_tools
from app.tools.context import ToolContext

TOOL_SPECS = [
    ToolSpec(
        name="search_products",
        description="Search the product catalog by free-text name, category, color, size, and/or price range.",
        parameters={
            "query": {"type": "string", "description": "Free-text product name search"},
            "category": {"type": "string", "description": "e.g. t-shirt, shirt, jeans, hoodie, jacket"},
            "color": {"type": "string"},
            "size": {"type": "string"},
            "min_price": {"type": "number"},
            "max_price": {"type": "number"},
            "on_sale": {"type": "boolean", "description": "True to only return products currently discounted (has a sale_price)"},
            "sort": {"type": "string", "enum": ["price_asc", "price_desc"], "description": "price_asc = cheapest first (for 'cheap'/'low price' requests), price_desc = most expensive first"},
            "limit": {"type": "integer", "default": 8},
        },
    ),
    ToolSpec(
        name="get_product_details",
        description="Get full details (description, price, all variants) for one specific product, identified by name, an ordinal reference like 'the second one', or a product_id.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string", "description": "e.g. 'the first one', 'প্রথমটা'"},
        },
    ),
    ToolSpec(
        name="check_product_stock",
        description="Check whether a specific product (optionally a specific size/color) is in stock and how many units remain.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string"},
            "size": {"type": "string"},
            "color": {"type": "string"},
        },
    ),
    ToolSpec(
        name="get_product_variants",
        description="List the available sizes and colors (with stock) for a specific product.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string"},
        },
    ),
    ToolSpec(
        name="add_to_cart",
        description="Add a quantity of a specific product (size/color) to the customer's cart.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string"},
            "size": {"type": "string"},
            "color": {"type": "string"},
            "quantity": {"type": "integer", "default": 1},
        },
    ),
    ToolSpec(
        name="remove_from_cart",
        description="Remove a specific product (size/color) from the customer's cart.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string"},
            "size": {"type": "string"},
            "color": {"type": "string"},
        },
    ),
    ToolSpec(
        name="update_cart_quantity",
        description="Change the quantity of an item already in the cart.",
        parameters={
            "product_id": {"type": "string"},
            "product_query": {"type": "string"},
            "reference": {"type": "string"},
            "size": {"type": "string"},
            "color": {"type": "string"},
            "quantity": {"type": "integer"},
        },
    ),
    ToolSpec(
        name="get_cart",
        description="Show everything currently in the customer's cart.",
        parameters={},
    ),
    ToolSpec(
        name="calculate_cart_total",
        description="Calculate the subtotal, delivery charge and total for the customer's current cart.",
        parameters={},
    ),
    ToolSpec(
        name="create_demo_order",
        description="Create a demo order from the customer's current cart. Requires customer_name, customer_phone, customer_address, and payment_method (demo_cod, demo_card, or demo_mobile).",
        parameters={
            "customer_name": {"type": "string"},
            "customer_phone": {"type": "string"},
            "customer_address": {"type": "string"},
            "payment_method": {"type": "string", "enum": ["demo_cod", "demo_card", "demo_mobile"]},
        },
    ),
    ToolSpec(
        name="get_order",
        description="Look up a single order by its order number.",
        parameters={
            "order_number": {"type": "string"},
            "customer_phone": {"type": "string", "description": "Phone used when ordering; required for orders not placed in this chat"},
        },
    ),
    ToolSpec(
        name="get_customer_orders",
        description="List all past orders for a customer, identified by phone number.",
        parameters={"customer_phone": {"type": "string"}},
    ),
    ToolSpec(
        name="cancel_demo_order",
        description="Cancel a demo order, if it is still in a cancellable state (PENDING or CONFIRMED).",
        parameters={
            "order_number": {"type": "string"},
            "customer_phone": {"type": "string", "description": "Phone used when ordering; required for orders not placed in this chat"},
        },
    ),
    ToolSpec(
        name="check_order_status",
        description="Check the current order_status and payment_status of an order.",
        parameters={
            "order_number": {"type": "string"},
            "customer_phone": {"type": "string", "description": "Phone used when ordering; required for orders not placed in this chat"},
        },
    ),
    ToolSpec(
        name="recommend_products",
        description="Recommend a few in-stock products, optionally within a category.",
        parameters={"category": {"type": "string"}, "limit": {"type": "integer", "default": 4}},
    ),
]

TOOL_FUNCTIONS: Dict[str, Callable[[Dict[str, Any], ToolContext], Dict[str, Any]]] = {
    "search_products": product_tools.search_products,
    "get_product_details": product_tools.get_product_details,
    "check_product_stock": product_tools.check_product_stock,
    "get_product_variants": product_tools.get_product_variants,
    "recommend_products": product_tools.recommend_products,
    "add_to_cart": cart_tools.add_to_cart,
    "remove_from_cart": cart_tools.remove_from_cart,
    "update_cart_quantity": cart_tools.update_cart_quantity,
    "get_cart": cart_tools.get_cart,
    "calculate_cart_total": cart_tools.calculate_cart_total,
    "create_demo_order": order_tools.create_demo_order,
    "get_order": order_tools.get_order,
    "get_customer_orders": order_tools.get_customer_orders,
    "cancel_demo_order": order_tools.cancel_demo_order,
    "check_order_status": order_tools.check_order_status,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    fn = TOOL_FUNCTIONS.get(tool_name)
    if not fn:
        return {"success": False, "data": None, "error": f"Unknown tool: {tool_name}"}
    try:
        return fn(arguments or {}, ctx)
    except Exception as e:  # noqa: BLE001 - tool failures must never crash the chat endpoint
        return {"success": False, "data": None, "error": f"Tool execution failed: {e}"}
