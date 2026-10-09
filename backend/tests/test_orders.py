import pytest

from app.models.order import OrderStatus
from app.services import cart_service, order_service, product_service


def _add_one_tshirt(db, sample_catalog, session_id, qty=1):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")
    cart_service.add_to_cart(db, session_id, variant.id, qty)
    return variant


def test_create_order_from_cart(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id, qty=2)

    order = order_service.create_demo_order(
        db, session_id,
        customer_name="Karim Ahmed",
        customer_phone="01711223344",
        customer_address="12 Dhanmondi, Dhaka",
        payment_method="demo_cod",
    )

    assert order.order_number.startswith("DEMO-")
    assert order.order_status == OrderStatus.pending
    assert len(order.items) == 1
    assert order.items[0].quantity == 2
    assert float(order.subtotal) == 1300.0


def test_order_total_matches_backend_calculation_not_client(db, sample_catalog, session_id):
    """Regression guard: totals must always be recomputed server-side from
    the cart, never trusted from client/AI input (spec section 13)."""
    _add_one_tshirt(db, sample_catalog, session_id, qty=3)
    expected = cart_service.calculate_cart_total(db, session_id)

    order = order_service.create_demo_order(
        db, session_id, "Test User", "01700000000", "Some address", "demo_cod",
    )
    assert float(order.total) == expected["total"]
    assert float(order.subtotal) == expected["subtotal"]


def test_create_order_decrements_stock(db, sample_catalog, session_id):
    variant = _add_one_tshirt(db, sample_catalog, session_id, qty=3)
    stock_before = variant.stock

    order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")

    db.refresh(variant)
    assert variant.stock == stock_before - 3


def test_create_order_simulates_demo_payment_success(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order = order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_card")

    assert order.payment_status == "DEMO_SUCCESS"
    assert order.payment is not None
    assert order.payment.status == "DEMO_SUCCESS"
    assert order.payment.transaction_ref.startswith("DEMO-TXN-")
    assert float(order.payment.amount) == float(order.total)


def test_create_order_empty_cart_raises(db, sample_catalog, session_id):
    with pytest.raises(order_service.EmptyCartError):
        order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")


def test_create_order_invalid_payment_method_raises(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    with pytest.raises(order_service.InvalidPaymentMethodError):
        order_service.create_demo_order(db, session_id, "A", "017", "addr", "real_visa_card")


def test_create_order_clears_cart_after_success(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")

    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["items"] == []


def test_check_order_status(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order = order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")

    status = order_service.check_order_status(db, order.order_number)
    assert status["order_status"] == "PENDING"
    assert status["payment_status"] == "DEMO_SUCCESS"


def test_check_order_status_not_found_raises(db, sample_catalog):
    with pytest.raises(order_service.OrderNotFoundError):
        order_service.check_order_status(db, "DEMO-9999")


def test_cancel_order_restocks_items(db, sample_catalog, session_id):
    variant = _add_one_tshirt(db, sample_catalog, session_id, qty=2)
    order = order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")
    db.refresh(variant)
    stock_after_order = variant.stock

    order_service.cancel_demo_order(db, order.order_number)

    db.refresh(variant)
    assert variant.stock == stock_after_order + 2


def test_cancel_order_updates_status(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order = order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")

    cancelled = order_service.cancel_demo_order(db, order.order_number)
    assert cancelled.order_status == OrderStatus.cancelled


def test_cancel_already_delivered_order_raises(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order = order_service.create_demo_order(db, session_id, "A", "017", "addr", "demo_cod")
    order.order_status = OrderStatus.delivered
    db.commit()

    with pytest.raises(order_service.OrderNotCancellableError):
        order_service.cancel_demo_order(db, order.order_number)


def test_get_customer_orders_by_phone(db, sample_catalog, session_id):
    _add_one_tshirt(db, sample_catalog, session_id)
    order_service.create_demo_order(db, session_id, "A", "01799998888", "addr", "demo_cod")

    orders = order_service.get_customer_orders(db, "01799998888")
    assert len(orders) == 1
    assert orders[0].customer_phone == "01799998888"
