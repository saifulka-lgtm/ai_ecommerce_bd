"""AI fulfillment agent — orders move forward on their own, never backwards."""
from datetime import datetime, timedelta

from app.models.order import Order, OrderStatus
from app.models.order_event import OrderStatusEvent
from app.services import fulfillment_service as fs


def _order(db, sample_catalog, status=OrderStatus.pending, age_seconds=0, number="DEMO-1111"):
    order = Order(
        order_number=number, customer_name="Rahim", customer_phone="01712345678",
        customer_address="Dhaka", subtotal=650, delivery_charge=60, discount=0, total=710,
        payment_method="demo_cod", payment_status="DEMO_SUCCESS", order_status=status,
    )
    db.add(order)
    db.commit()
    order.updated_at = datetime.utcnow() - timedelta(seconds=age_seconds)
    db.commit()
    return order


def test_order_not_advanced_before_wait_time(db, sample_catalog):
    _order(db, sample_catalog, age_seconds=5)
    assert fs.advance_orders(db, 30, 90, 180) == []


def test_order_advances_one_step_per_run_through_to_delivered(db, sample_catalog):
    o = _order(db, sample_catalog, age_seconds=1000)
    now = datetime.utcnow()
    assert fs.advance_orders(db, 30, 90, 180, now=now)[0]["to"] == "CONFIRMED"
    # Just advanced -> must wait again, so a second immediate run does nothing.
    assert fs.advance_orders(db, 30, 90, 180, now=now) == []
    assert fs.advance_orders(db, 30, 90, 180, now=now + timedelta(seconds=100))[0]["to"] == "SHIPPED"
    assert fs.advance_orders(db, 30, 90, 180, now=now + timedelta(seconds=400))[0]["to"] == "DELIVERED"
    db.refresh(o)
    assert o.order_status == OrderStatus.delivered
    assert db.query(OrderStatusEvent).count() == 3


def test_delivered_and_cancelled_orders_are_never_touched(db, sample_catalog):
    _order(db, sample_catalog, OrderStatus.delivered, 99999, "DEMO-2222")
    _order(db, sample_catalog, OrderStatus.cancelled, 99999, "DEMO-3333")
    assert fs.advance_orders(db, 0, 0, 0) == []


def test_admin_can_see_fulfillment_events(client, db, sample_catalog):
    _order(db, sample_catalog, age_seconds=1000)
    fs.advance_orders(db, 30, 90, 180)
    token = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    res = client.get("/api/admin/fulfillment-events", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()[0]["actor"] == "AI Fulfillment Agent"
    assert client.get("/api/admin/fulfillment-events").status_code == 401
