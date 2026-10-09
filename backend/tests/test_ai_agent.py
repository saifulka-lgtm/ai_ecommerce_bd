"""
AI agent / tool-selection tests — verifies the mock provider picks the
correct tool for Bangla and English requests, and that the agent never
answers with data that didn't come back from a tool.
"""
from app.ai.agent import handle_message
from app.models.ai_conversation import AIToolLog


def test_english_search_selects_search_products_tool(db, sample_catalog, session_id):
    result = handle_message(db, session_id, "Show me black t-shirts under 1000 taka")
    assert result["tool_used"] == "search_products"
    assert result["language"] == "en"
    assert len(result["data"]["products"]) == 1
    assert result["data"]["products"][0]["name"] == "Basic Cotton T-Shirt"


def test_bangla_search_selects_search_products_tool(db, sample_catalog, session_id):
    result = handle_message(db, session_id, "আমাকে ১০০০ টাকার মধ্যে কালো টি-শার্ট দেখাও।")
    assert result["tool_used"] == "search_products"
    assert result["language"] == "bn"
    assert len(result["data"]["products"]) == 1


def test_search_for_unavailable_category_returns_empty_not_invented(db, sample_catalog, session_id):
    result = handle_message(db, session_id, "Show me red shoes")
    assert result["tool_used"] == "search_products"
    assert result["data"]["products"] == []
    # The reply must not claim to have found something
    assert "found 0" in result["reply"].lower() or "couldn't find" in result["reply"].lower()


def test_price_inquiry_uses_real_product_data(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    result = handle_message(db, session_id, "How much is it?")
    assert result["tool_used"] == "get_product_details"
    assert "650" in result["reply"]  # the real DB price, not invented


def test_ordinal_reference_resolves_to_previously_shown_product(db, sample_catalog, session_id):
    search = handle_message(db, session_id, "Show me black t-shirts")
    assert len(search["data"]["products"]) == 1
    result = handle_message(db, session_id, "প্রথমটার দাম কত?")
    assert result["tool_used"] == "get_product_details"
    assert result["data"]["products"][0]["name"] == "Basic Cotton T-Shirt"


def test_add_to_cart_via_chat_checks_real_stock(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    result = handle_message(db, session_id, "Add 1 S size black to cart")
    assert result["tool_used"] == "add_to_cart"
    assert result["data"]["item_count"] == 1


def test_add_to_cart_over_stock_reports_error_not_success(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    # M/Black only has 5 in stock
    result = handle_message(db, session_id, "Add 99 M size black to cart")
    log = db.query(AIToolLog).order_by(AIToolLog.created_at.desc()).first()
    assert log.tool_name == "add_to_cart"
    assert log.success is False


def test_order_flow_asks_for_missing_fields_then_creates_order(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    handle_message(db, session_id, "Add 1 S size black to cart")

    ask = handle_message(db, session_id, "I want to place an order")
    assert ask["tool_used"] == "create_demo_order"
    log = db.query(AIToolLog).filter(AIToolLog.tool_name == "create_demo_order").order_by(AIToolLog.created_at.desc()).first()
    assert log.success is False
    assert "missing_fields" in (log.tool_result.get("data") or {})

    complete = handle_message(
        db, session_id,
        "My name is Karim Ahmed, phone 01711223344, address 12 Dhanmondi Dhaka, cash on delivery",
    )
    assert complete["tool_used"] == "create_demo_order"
    assert "DEMO-" in complete["reply"]
    assert complete["data"]["order_number"].startswith("DEMO-")


def test_order_status_check_via_chat(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    handle_message(db, session_id, "Add 1 S size black to cart")
    handle_message(db, session_id, "I want to place an order")
    handle_message(
        db, session_id,
        "My name is Karim, phone 01711223344, address Dhaka, cash on delivery",
    )
    result = handle_message(db, session_id, "What is my order status?")
    assert result["tool_used"] == "check_order_status"
    assert "PENDING" in result["reply"]


def test_every_tool_call_is_logged(db, sample_catalog, session_id):
    handle_message(db, session_id, "Show me black t-shirts")
    logs = db.query(AIToolLog).all()
    assert len(logs) == 1
    assert logs[0].tool_name == "search_products"
    assert logs[0].customer_message == "Show me black t-shirts"
    assert logs[0].success is True


def test_greeting_does_not_call_any_tool(db, sample_catalog, session_id):
    result = handle_message(db, session_id, "Hello")
    assert result["tool_used"] is None
    logs = db.query(AIToolLog).all()
    assert logs == []
