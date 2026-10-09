"""
Turns a tool's structured result into a short natural-language reply.
Every value used here comes straight from tool_result — nothing is
invented. Used by MockAIProvider, and available as a safety-net formatter
for the real providers too.
"""
from typing import Any, Dict

from app.ai.constants import MISSING_FIELD_PROMPTS

NOT_FOUND = {
    "en": "Sorry, I couldn't find any products matching that right now — want me to show you a different category?",
    "bn": "দুঃখিত, বর্তমানে এই ধরনের কোনো প্রোডাক্ট পাওয়া যায়নি, আপনি চাইলে আমি অন্য category দেখাতে পারি।",
}


def render_reply(tool_name: str, tool_result: Dict[str, Any], language: str) -> str:
    success = tool_result.get("success")
    data = tool_result.get("data") or {}
    error = tool_result.get("error")

    if not success:
        return _error_reply(data, error, language)

    handler = _HANDLERS.get(tool_name)
    if not handler:
        return "Done." if language == "en" else "সম্পন্ন হয়েছে।"
    return handler(data, language)


def _error_reply(data: Dict[str, Any], error: str, language: str) -> str:
    data = data or {}

    if data.get("missing_fields"):
        labels = [MISSING_FIELD_PROMPTS.get(f, {}).get(language, f) for f in data["missing_fields"]]
        joined = ", ".join(labels)
        if language == "bn":
            return f"অর্ডার সম্পূর্ণ করতে দয়া করে দিন: {joined}।"
        return f"To complete your order, please share: {joined}."

    if data.get("available_variants"):
        variants = data["available_variants"]
        listing = "; ".join(f"{v['size']}/{v['color']} ({v['stock']} in stock)" for v in variants)
        name = data.get("product_name", "this product")
        if language == "bn":
            return f"{name}-এর জন্য উপলব্ধ: {listing}। কোনটা চান?"
        return f"Available options for {name}: {listing}. Which would you like?"

    if language == "bn":
        return f"দুঃখিত, এই মুহূর্তে সেটা করা গেল না। ({error})"
    return f"Sorry, I couldn't do that. ({error})"


def _search_products(data, language):
    products = data.get("products") or []
    count = data.get("count", 0)
    if count == 0:
        return NOT_FOUND[language]

    # discount_percent is always computed server-side from real price/
    # sale_price (see product_service.to_list_item) — never invented here.
    discounted = [p for p in products if p.get("discount_percent")]

    # Price-ranked request ("cheap" / "low price" / "expensive"): say so, and
    # name the first result's real price so the ordering is visible in text.
    sorted_by = data.get("sorted_by")
    if sorted_by in ("price_asc", "price_desc") and products:
        first = products[0]
        if language == "bn":
            order_bn = "কম থেকে বেশি" if sorted_by == "price_asc" else "বেশি থেকে কম"
            return (
                f"দাম {order_bn} সাজিয়ে {count}টি প্রোডাক্ট দেখাচ্ছি। "
                f"প্রথমটি {first['name']} — ৳{first['effective_price']:.0f}।"
            )
        order_en = "lowest to highest" if sorted_by == "price_asc" else "highest to lowest"
        return (
            f"Here are {count} product(s) sorted by price, {order_en}. "
            f"First up: {first['name']} at ৳{first['effective_price']:.0f}."
        )

    if language == "bn":
        base = f"আমি আপনার জন্য {count}টি প্রোডাক্ট পেয়েছি।"
        if discounted:
            lines = "; ".join(
                f"{p['name']} — {p['discount_percent']}% ছাড়ে ৳{p['effective_price']:.0f} (আগে ৳{p['price']:.0f})"
                for p in discounted[:5]
            )
            base += f" ছাড়ে আছে: {lines}।"
        return base

    base = f"I found {count} product(s) matching your search."
    if discounted:
        lines = "; ".join(
            f"{p['name']} — {p['discount_percent']}% off, now ৳{p['effective_price']:.0f} (was ৳{p['price']:.0f})"
            for p in discounted[:5]
        )
        base += f" On sale: {lines}."
    return base


def _product_details(data, language):
    p = data["product"]
    price = p["effective_price"]
    sizes = ", ".join(p["sizes"]) or "-"
    colors = ", ".join(p["colors"]) or "-"
    discount = p.get("discount_percent")
    discount_bn = f" ({discount}% ছাড়ে, আগে ৳{p['price']:.0f} ছিল)" if discount else ""
    discount_en = f" ({discount}% off, was ৳{p['price']:.0f})" if discount else ""
    if language == "bn":
        return f"{p['name']} এর দাম ৳{price:.0f}{discount_bn}। সাইজ: {sizes}, কালার: {colors}। স্টকে আছে: {p['total_stock']} পিস।"
    return f"{p['name']} costs ৳{price:.0f}{discount_en}. Sizes: {sizes}. Colors: {colors}. {p['total_stock']} in stock."


def _check_stock(data, language):
    if "stock" in data and "size" in data:
        status_en = "in stock" if data["in_stock"] else "out of stock"
        status_bn = "স্টকে আছে" if data["in_stock"] else "স্টকে নেই"
        if language == "bn":
            return f"{data['product_name']} ({data['size']}/{data['color']}) — {status_bn}, {data['stock']} পিস।"
        return f"{data['product_name']} in {data['size']}/{data['color']} is {status_en} ({data['stock']} left)."
    total = data.get("total_stock", 0)
    if language == "bn":
        return f"{data['product_name']} এর মোট স্টক {total} পিস।"
    return f"{data['product_name']} has {total} unit(s) in stock across all variants."


def _variants(data, language):
    sizes = ", ".join(data["sizes"]) or "-"
    colors = ", ".join(data["colors"]) or "-"
    if language == "bn":
        return f"{data['product_name']} পাওয়া যাচ্ছে সাইজ: {sizes} এবং কালার: {colors} এ।"
    return f"{data['product_name']} is available in sizes {sizes} and colors {colors}."


def _cart_reply(prefix_en: str, prefix_bn: str):
    def _handler(data, language):
        item_count = data.get("item_count", 0)
        total = data.get("total", 0)
        if item_count == 0:
            return (prefix_bn + "আপনার কার্ট খালি।") if language == "bn" else (prefix_en + "Your cart is empty.")
        if language == "bn":
            return f"{prefix_bn}কার্টে {item_count}টি আইটেম, সর্বমোট ৳{total:.0f} (ডেলিভারি চার্জসহ)।"
        return f"{prefix_en}Your cart has {item_count} item(s), total ৳{total:.0f} (incl. delivery)."
    return _handler


def _create_order(data, language):
    if language == "bn":
        return (
            f"আপনার অর্ডার সফলভাবে তৈরি হয়েছে!\nঅর্ডার আইডি: {data['order_number']}\n"
            f"মোট: ৳{data['total']:.0f}\nপেমেন্ট: {data['payment_status']}\nঅবস্থা: {data['order_status']}"
        )
    return (
        f"Order successfully created!\nOrder ID: {data['order_number']}\n"
        f"Total: ৳{data['total']:.0f}\nPayment: {data['payment_status']}\nStatus: {data['order_status']}"
    )


STATUS_TEXT = {
    "PENDING": {"en": "pending", "bn": "অপেক্ষমাণ"},
    "CONFIRMED": {"en": "confirmed", "bn": "কনফার্মড"},
    "PROCESSING": {"en": "being processed", "bn": "প্রসেসিং চলছে"},
    "SHIPPED": {"en": "shipped", "bn": "শিপ করা হয়েছে"},
    "DELIVERED": {"en": "delivered", "bn": "ডেলিভারি সম্পন্ন হয়েছে"},
    "CANCELLED": {"en": "cancelled", "bn": "বাতিল করা হয়েছে"},
}


def _get_order(data, language):
    status = data["order_status"]
    status_txt = STATUS_TEXT.get(status, {}).get(language, status)
    items = data.get("items") or []
    if language == "bn":
        lines = [f"অর্ডার {data['order_number']} — অবস্থা: {status_txt}।"]
        for i in items:
            lines.append(f"• {i['product_name']} ({i['size']}/{i['color']}) × {i['quantity']} = ৳{i['subtotal']:.0f}")
        lines.append(f"ঠিকানা: {data['customer_address']}")
        lines.append(
            f"সাবটোটাল ৳{data['subtotal']:.0f}, ডেলিভারি চার্জ ৳{data['delivery_charge']:.0f}, "
            f"মোট ৳{data['total']:.0f}। পেমেন্ট: {data['payment_status']}।"
        )
        return "\n".join(lines)
    lines = [f"Order {data['order_number']} — status: {status_txt}."]
    for i in items:
        lines.append(f"• {i['product_name']} ({i['size']}/{i['color']}) x {i['quantity']} = ৳{i['subtotal']:.0f}")
    lines.append(f"Address: {data['customer_address']}")
    lines.append(
        f"Subtotal ৳{data['subtotal']:.0f}, delivery ৳{data['delivery_charge']:.0f}, "
        f"total ৳{data['total']:.0f}. Payment: {data['payment_status']}."
    )
    return "\n".join(lines)


def _customer_orders(data, language):
    count = data.get("count", 0)
    if count == 0:
        return "এই নম্বরে কোনো অর্ডার পাওয়া যায়নি।" if language == "bn" else "No orders found for that phone number."
    return f"আপনার {count}টি অর্ডার পাওয়া গেছে।" if language == "bn" else f"Found {count} order(s) for you."


def _cancel_order(data, language):
    if language == "bn":
        return f"অর্ডার {data['order_number']} বাতিল করা হয়েছে।"
    return f"Order {data['order_number']} has been cancelled."


def _order_status(data, language):
    if language == "bn":
        return f"অর্ডার {data['order_number']} — অবস্থা: {data['order_status']}, পেমেন্ট: {data['payment_status']}।"
    return f"Order {data['order_number']} — status: {data['order_status']}, payment: {data['payment_status']}."


def _recommend(data, language):
    count = data.get("count", 0)
    if count == 0:
        return "দুঃখিত, এই মুহূর্তে কোনো সাজেশন নেই।" if language == "bn" else "Sorry, nothing to recommend right now."
    return f"আপনার জন্য {count}টি প্রোডাক্ট সাজেস্ট করছি।" if language == "bn" else f"Here are {count} product(s) I'd recommend."


_HANDLERS = {
    "search_products": _search_products,
    "get_product_details": _product_details,
    "check_product_stock": _check_stock,
    "get_product_variants": _variants,
    "add_to_cart": _cart_reply("Added to your cart. ", "প্রোডাক্টটি কার্টে যোগ করা হয়েছে। "),
    "remove_from_cart": _cart_reply("Removed from your cart. ", "প্রোডাক্টটি কার্ট থেকে সরানো হয়েছে। "),
    "update_cart_quantity": _cart_reply("Cart updated. ", "কার্ট আপডেট করা হয়েছে। "),
    "get_cart": _cart_reply("", ""),
    "calculate_cart_total": _cart_reply("", ""),
    "create_demo_order": _create_order,
    "get_order": _get_order,
    "get_customer_orders": _customer_orders,
    "cancel_demo_order": _cancel_order,
    "check_order_status": _order_status,
    "recommend_products": _recommend,
}
