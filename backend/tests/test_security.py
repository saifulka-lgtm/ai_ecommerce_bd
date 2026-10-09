"""Privacy / security: orders must not be readable by strangers."""
import re

from app.ai.agent import handle_message
from app.services import order_service


def _place(db, session_id, phone="01712345678"):
    handle_message(db, session_id, "Show me black t-shirts")
    handle_message(db, session_id, "Add the first one to cart size M black")
    handle_message(db, session_id, "I want to place an order")
    placed = handle_message(
        db, session_id,
        f"Name: Rahim, phone {phone}, address: House 5, Road 3, Dhaka, payment demo_cod",
    )
    return placed["data"]["order_number"]


def test_order_numbers_are_long_and_random():
    from app.utils.generators import generate_order_number
    numbers = {generate_order_number() for _ in range(200)}
    assert len(numbers) == 200
    assert all(re.fullmatch(r"DEMO-\d{8}", n) for n in numbers)


def test_stranger_cannot_read_someone_elses_order_by_number(db, sample_catalog):
    number = _place(db, "session-owner")
    res = handle_message(db, "session-stranger", f"Show details of order {number}")
    assert "Rahim" not in res["reply"] and "House 5" not in res["reply"]
    assert res["data"] is None
    assert "phone" in res["reply"].lower()


def test_wrong_phone_and_unknown_order_give_the_same_answer(db, sample_catalog):
    number = _place(db, "session-owner")
    wrong = handle_message(db, "s2", f"Show details of order {number} phone 01999999999")
    unknown = handle_message(db, "s3", "Show details of order DEMO-00000000 phone 01999999999")
    assert wrong["reply"] == unknown["reply"]
    assert "House 5" not in wrong["reply"]


def test_correct_phone_unlocks_the_order(db, sample_catalog):
    number = _place(db, "session-owner")
    ok = handle_message(db, "s4", f"Show details of order {number} phone +8801712345678")
    assert ok["tool_used"] == "get_order"
    assert "House 5" in ok["reply"]


def test_stranger_cannot_cancel_someone_elses_order(db, sample_catalog):
    number = _place(db, "session-owner")
    res = handle_message(db, "s5", f"cancel order {number}")
    assert "cancelled" not in res["reply"].lower() and "বাতিল করা হয়েছে" not in res["reply"]
    assert order_service.get_order_by_number(db, number).order_status.value == "PENDING"


def test_my_orders_list_is_summary_only(db, sample_catalog):
    _place(db, "session-owner")
    res = handle_message(db, "s6", "my orders 01712345678")
    assert res["tool_used"] == "get_customer_orders"
    order = res["data"]["orders"][0]
    assert "customer_address" not in order and "items" not in order and "customer_phone" not in order


def test_rest_order_endpoints_require_matching_phone(client, db, sample_catalog):
    from tests.test_api import _make_order
    number = _make_order(client, db, sample_catalog)
    assert client.get(f"/api/orders/{number}").status_code == 422             # phone missing
    assert client.get(f"/api/orders/{number}?phone=01999999999").status_code == 404
    assert client.get(f"/api/orders/{number}?phone=01712345678").status_code == 200
    assert client.post(f"/api/orders/{number}/cancel?phone=01999999999").status_code == 404
    listing = client.get("/api/orders?phone=01712345678").json()
    assert "customer_address" not in listing[0]


# ---- Stock race, rate limit, admin hardening ----

def test_last_unit_can_only_be_bought_once_even_concurrently(db, sample_catalog):
    import threading
    from tests.conftest import TestSessionLocal
    from app.services import cart_service
    from app.models.product import ProductVariant

    variant = sample_catalog["variants"][1]       # T-Shirt M/Black
    variant.stock = 1
    db.commit()
    vid = variant.id

    for sid in ("race-a", "race-b"):
        cart_service.add_to_cart(db, sid, vid, 1)

    barrier = threading.Barrier(2)
    results = {}

    def buy(sid):
        s = TestSessionLocal()
        try:
            barrier.wait()
            order_service.create_demo_order(s, sid, "X", "01712345678", "Dhaka", "demo_cod")
            results[sid] = "ok"
        except Exception as e:  # noqa: BLE001
            results[sid] = type(e).__name__
        finally:
            s.close()

    threads = [threading.Thread(target=buy, args=(sid,)) for sid in ("race-a", "race-b")]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert sorted(results.values()) == ["InsufficientStockError", "ok"], results
    db.expire_all()
    assert db.query(ProductVariant).filter(ProductVariant.id == vid).one().stock == 0


def test_rate_limiter_blocks_after_limit_and_recovers():
    from app.utils.rate_limit import RateLimiter
    rl = RateLimiter(max_calls=3, window_seconds=60)
    assert [rl.allow("ip", now=t) for t in (0, 1, 2)] == [True, True, True]
    assert rl.allow("ip", now=3) is False
    assert rl.allow("other-ip", now=3) is True
    assert rl.allow("ip", now=61) is True      # window passed


def test_login_endpoint_is_rate_limited(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    from app.api import admin as admin_api
    admin_api._login_limiter._hits.clear()
    codes = [client.post("/api/admin/login", json={"username": "admin", "password": "bad"}).status_code for _ in range(7)]
    assert codes[:5] == [401] * 5 and codes[5:] == [429, 429]
    admin_api._login_limiter._hits.clear()


def test_password_hash_login_and_wrong_password(monkeypatch):
    from app.config import get_settings
    from app.services import auth_service
    s = get_settings()
    monkeypatch.setattr(s, "admin_password_hash", auth_service.hash_password("a-Strong-pass-1"))
    assert auth_service.authenticate_admin("admin", "a-Strong-pass-1")
    import pytest
    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.authenticate_admin("admin", "admin123")


def test_production_refuses_default_secrets():
    import pytest
    from app.config import Settings
    with pytest.raises(ValueError):
        Settings(environment="production")
    ok = Settings(environment="production", secret_key="x" * 40, admin_password_hash="pbkdf2_sha256$1$aa$bb")
    assert ok.environment == "production"
