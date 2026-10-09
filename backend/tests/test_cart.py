import pytest

from app.services import cart_service, product_service


def test_add_to_cart_happy_path(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")

    cart_service.add_to_cart(db, session_id, variant.id, 2)
    totals = cart_service.calculate_cart_total(db, session_id)

    assert totals["item_count"] == 2
    assert len(totals["items"]) == 1
    assert totals["items"][0]["quantity"] == 2
    assert totals["subtotal"] == 1300.0  # 650 * 2


def test_add_to_cart_insufficient_stock_raises(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="M", color="Black")  # stock=5

    with pytest.raises(cart_service.InsufficientStockError):
        cart_service.add_to_cart(db, session_id, variant.id, 6)


def test_add_to_cart_same_variant_twice_accumulates(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")  # stock=10

    cart_service.add_to_cart(db, session_id, variant.id, 3)
    cart_service.add_to_cart(db, session_id, variant.id, 2)

    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["items"][0]["quantity"] == 5


def test_update_cart_quantity(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")
    cart_service.add_to_cart(db, session_id, variant.id, 1)

    cart_service.update_cart_quantity(db, session_id, variant.id, 4)
    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["items"][0]["quantity"] == 4


def test_remove_from_cart(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")
    cart_service.add_to_cart(db, session_id, variant.id, 1)

    cart_service.remove_from_cart(db, session_id, variant.id)
    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["items"] == []
    assert totals["item_count"] == 0


def test_cart_total_includes_delivery_charge_below_threshold(db, sample_catalog, session_id):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")
    cart_service.add_to_cart(db, session_id, variant.id, 1)  # 650, below free-delivery threshold

    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["delivery_charge"] > 0
    assert totals["total"] == totals["subtotal"] + totals["delivery_charge"]


def test_cart_total_free_delivery_above_threshold(db, sample_catalog, session_id):
    jeans = sample_catalog["jeans"]
    variant = product_service.find_variant(db, jeans.id, size="32", color="Blue")
    cart_service.add_to_cart(db, session_id, variant.id, 2)  # 1499*2 = 2998, above threshold

    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals["delivery_charge"] == 0
    assert totals["total"] == totals["subtotal"]


def test_empty_cart_totals_are_zero(db, sample_catalog, session_id):
    totals = cart_service.calculate_cart_total(db, session_id)
    assert totals == {
        "session_id": session_id,
        "items": [],
        "subtotal": 0.0,
        "delivery_charge": 0.0,
        "total": 0.0,
        "item_count": 0,
    }
