from app.services import product_service


def test_get_product_effective_price_no_discount(db, sample_catalog):
    jeans = sample_catalog["jeans"]
    assert jeans.effective_price == jeans.sale_price  # jeans has a sale price
    assert float(jeans.effective_price) == 1499.0


def test_get_product_effective_price_no_sale(db, sample_catalog):
    tshirt = sample_catalog["tshirt"]
    assert float(tshirt.effective_price) == 650.0


def test_check_stock_in_stock_variant(db, sample_catalog):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="S", color="Black")
    assert variant is not None
    assert variant.stock == 10
    assert product_service.check_stock(db, variant.id, requested_qty=5) is True


def test_check_stock_insufficient(db, sample_catalog):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="M", color="Black")
    assert variant.stock == 5
    assert product_service.check_stock(db, variant.id, requested_qty=6) is False


def test_check_stock_out_of_stock_variant(db, sample_catalog):
    tshirt = sample_catalog["tshirt"]
    variant = product_service.find_variant(db, tshirt.id, size="L", color="Black")
    assert variant.stock == 0
    assert product_service.check_stock(db, variant.id, requested_qty=1) is False


def test_total_stock_sums_all_variants(db, sample_catalog):
    tshirt = sample_catalog["tshirt"]
    db.refresh(tshirt)
    # S/Black=10, M/Black=5, L/Black=0, M/White=8
    assert tshirt.total_stock == 23


def test_low_stock_products(db, sample_catalog):
    low = product_service.low_stock_products(db, threshold=25)
    names = {p.name for p in low}
    assert "Basic Cotton T-Shirt" in names  # total_stock 23 <= 25
