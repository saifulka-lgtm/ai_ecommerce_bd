from app.services import product_service


def test_search_by_category(db, sample_catalog):
    results = product_service.search_products(db, category="t-shirt")
    assert len(results) == 1
    assert results[0].name == "Basic Cotton T-Shirt"


def test_search_by_category_does_not_cross_match(db, sample_catalog):
    # "shirt" must not also match "T-Shirts" or vice versa in a real catalog
    # with both Shirts and T-Shirts categories — regression test for the
    # substring-collision bug found during manual testing.
    results = product_service.search_products(db, category="jean")
    assert len(results) == 1
    assert results[0].name == "Slim Fit Jeans"


def test_search_by_color(db, sample_catalog):
    results = product_service.search_products(db, color="black")
    assert len(results) == 1
    assert results[0].name == "Basic Cotton T-Shirt"


def test_search_by_max_price(db, sample_catalog):
    results = product_service.search_products(db, max_price=1000)
    names = {p.name for p in results}
    assert names == {"Basic Cotton T-Shirt"}


def test_search_by_min_and_max_price(db, sample_catalog):
    results = product_service.search_products(db, min_price=1000, max_price=2000)
    names = {p.name for p in results}
    assert names == {"Slim Fit Jeans"}


def test_search_no_match_returns_empty_not_error(db, sample_catalog):
    results = product_service.search_products(db, category="shoes")
    assert results == []


def test_search_free_text_query(db, sample_catalog):
    results = product_service.search_products(db, query="Cotton")
    assert len(results) == 1
    assert results[0].sku == "TSH-TEST-001"


def test_inactive_products_excluded_by_default(db, sample_catalog):
    product = sample_catalog["tshirt"]
    product.active = False
    db.commit()
    results = product_service.search_products(db, query="Cotton")
    assert results == []
