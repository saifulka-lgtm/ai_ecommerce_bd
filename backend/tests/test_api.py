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
