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


# ---- Admin is track-only: no endpoint can change an order's status ----

def test_admin_cannot_change_order_status(client, db, sample_catalog):
    token = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.put(f"/api/admin/orders/{fake}/status", json={"order_status": "DELIVERED"}, headers=h).status_code in (404, 405)
    assert client.post("/api/admin/ai-chat", json={"message": "DEMO-1234 ship"}, headers=h).status_code in (404, 405)


# ---- Inventory tracking ----

def _make_order(client, db, sample_catalog):
    variant = sample_catalog["variants"][0]  # Basic Cotton T-Shirt S/Black, stock 10
    sid = "inventory-test"
    client.post("/api/cart/add", json={"session_id": sid, "variant_id": str(variant.id), "quantity": 1})
    res = client.post("/api/orders", json={
        "session_id": sid, "customer_name": "Rahim", "customer_phone": "01712345678",
        "customer_address": "Dhaka", "payment_method": "demo_cod",
    })
    assert res.status_code == 200, res.text
    return res.json()["order_number"]


def test_inventory_endpoints_require_auth(client):
    assert client.get("/api/admin/inventory").status_code == 401
    assert client.get("/api/admin/stock-movements").status_code == 401


def test_inventory_overview_and_movements_follow_orders(client, db, sample_catalog):
    token = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    inv = client.get("/api/admin/inventory", headers=h).json()
    assert inv["summary"]["total_products"] == 2
    assert inv["summary"]["total_units"] == 10 + 5 + 0 + 8 + 15
    assert inv["summary"]["out_of_stock_variants"] == 1       # the L/Black tee
    tee = next(p for p in inv["products"] if p["name"] == "Basic Cotton T-Shirt")
    assert tee["total_stock"] == 23 and tee["status"] == "LOW"  # has an out-of-stock variant

    # A sale reduces stock and is logged; cancelling restores it and is logged.
    number = _make_order(client, db, sample_catalog)
    mv = client.get("/api/admin/stock-movements", headers=h).json()
    assert mv[0]["change"] == -1 and number in mv[0]["reason"] and mv[0]["stock_after"] == 9

    client.post(f"/api/orders/{number}/cancel")
    mv = client.get("/api/admin/stock-movements", headers=h).json()
    assert mv[0]["change"] == 1 and mv[0]["stock_after"] == 10
    inv = client.get("/api/admin/inventory", headers=h).json()
    assert inv["summary"]["total_units"] == 38
