"""
REST API-level tests via FastAPI's TestClient — these exercise full request/
response validation (Pydantic response_model), which is what caught the
CartItemOut schema bug during manual testing (the service layer alone
wouldn't have surfaced it).
"""


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_products(client, sample_catalog):
    res = client.get("/api/products")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_cart_add_endpoint_matches_response_schema(client, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = next(v for v in tshirt.variants if v.size == "S" and v.color == "Black")

    res = client.post("/api/cart/add", json={"session_id": session_id, "variant_id": str(variant.id), "quantity": 1})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["items"][0]["variant_id"] == str(variant.id)
    assert body["item_count"] == 1


def test_cart_add_insufficient_stock_returns_400(client, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = next(v for v in tshirt.variants if v.size == "M" and v.color == "Black")  # stock=5

    res = client.post("/api/cart/add", json={"session_id": session_id, "variant_id": str(variant.id), "quantity": 999})
    assert res.status_code == 400


def test_order_creation_endpoint(client, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = next(v for v in tshirt.variants if v.size == "S" and v.color == "Black")
    client.post("/api/cart/add", json={"session_id": session_id, "variant_id": str(variant.id), "quantity": 1})

    res = client.post(
        "/api/orders",
        json={
            "session_id": session_id,
            "customer_name": "Test User",
            "customer_phone": "01711223344",
            "customer_address": "Dhaka",
            "payment_method": "demo_cod",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["order_number"].startswith("DEMO-")
    assert body["payment_status"] == "DEMO_SUCCESS"


def test_admin_endpoints_require_auth(client):
    res = client.get("/api/admin/dashboard")
    assert res.status_code == 401


def test_admin_login_and_dashboard(client, sample_catalog):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["total_products"] == 2


def test_admin_login_wrong_password_rejected(client):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_chat_endpoint(client, sample_catalog, session_id):
    res = client.post("/api/chat", json={"session_id": session_id, "message": "Show me black t-shirts"})
    assert res.status_code == 200
    body = res.json()
    assert body["tool_used"] == "search_products"
    assert len(body["data"]["products"]) == 1


# ---- Admin AI order assistant ----

def _admin_headers(client):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_order(client, db, sample_catalog):
    from app.models.product import ProductVariant
    variant = sample_catalog["variants"][0]
    sid = "admin-ai-test"
    client.post("/api/cart/add", json={"session_id": sid, "variant_id": str(variant.id), "quantity": 1})
    res = client.post("/api/orders", json={
        "session_id": sid, "customer_name": "Rahim", "customer_phone": "01712345678",
        "customer_address": "Dhaka", "payment_method": "demo_cod",
    })
    assert res.status_code == 200, res.text
    return res.json()["order_number"]


def test_admin_ai_chat_requires_auth(client):
    res = client.post("/api/admin/ai-chat", json={"message": "DEMO-1234 ship"})
    assert res.status_code == 401


def test_admin_ai_chat_updates_status_bangla_and_english(client, db, sample_catalog):
    number = _make_order(client, db, sample_catalog)
    h = _admin_headers(client)

    res = client.post("/api/admin/ai-chat", json={"message": f"{number} শিপ করো"}, headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["changed"] is True
    assert body["orders"][0]["order_status"] == "SHIPPED"

    res = client.post("/api/admin/ai-chat", json={"message": f"mark {number} as delivered"}, headers=h)
    assert res.json()["orders"][0]["order_status"] == "DELIVERED"

    # DELIVERED is final
    res = client.post("/api/admin/ai-chat", json={"message": f"{number} cancel"}, headers=h)
    assert res.json()["changed"] is False
    assert res.json()["orders"][0]["order_status"] == "DELIVERED"


def test_admin_ai_chat_lists_orders_and_handles_unknown(client, db, sample_catalog):
    number = _make_order(client, db, sample_catalog)
    h = _admin_headers(client)
    res = client.post("/api/admin/ai-chat", json={"message": "show pending orders"}, headers=h)
    assert number in res.json()["reply"]
    res = client.post("/api/admin/ai-chat", json={"message": "DEMO-0000 ship"}, headers=h)
    assert "not found" in res.json()["reply"]
    res = client.post("/api/admin/ai-chat", json={"message": "hello"}, headers=h)
    assert res.json()["orders"] == []
