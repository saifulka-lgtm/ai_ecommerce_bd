"""
Test fixtures. Uses a separate PostgreSQL database (ai_ecommerce_bd_test) so
tests never touch real demo/dev data. Tables are dropped and recreated
before each test for full isolation.
"""
import os
import uuid

import psycopg2
import pytest
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_ecommerce_bd_test")
os.environ.setdefault("AI_PROVIDER", "mock")
# The background fulfillment loop must not touch the test database.
os.environ.setdefault("AUTO_FULFILLMENT_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

TEST_DB_NAME = "ai_ecommerce_bd_test"
ADMIN_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"


def _ensure_test_database():
    conn = psycopg2.connect(ADMIN_DSN)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
        if not cur.fetchone():
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB_NAME)))
    conn.close()


_ensure_test_database()

from app.database import Base  # noqa: E402
from app import models  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.product import Product, ProductVariant  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_catalog(db):
    """A small, deterministic catalog: one T-Shirt (Black/White x S/M/L),
    one out-of-stock variant, and one Jeans product — enough to exercise
    search, stock, cart and order logic without depending on seed.py."""
    tshirt_cat = Category(name="T-Shirts", slug="t-shirts")
    jeans_cat = Category(name="Jeans", slug="jeans")
    db.add_all([tshirt_cat, jeans_cat])
    db.flush()

    tshirt = Product(
        name="Basic Cotton T-Shirt",
        description="A basic tee.",
        category_id=tshirt_cat.id,
        price=650,
        sale_price=None,
        sku="TSH-TEST-001",
        image="https://example.com/tshirt.jpg",
        active=True,
    )
    db.add(tshirt)
    db.flush()

    variants = [
        ProductVariant(product_id=tshirt.id, size="S", color="Black", stock=10),
        ProductVariant(product_id=tshirt.id, size="M", color="Black", stock=5),
        ProductVariant(product_id=tshirt.id, size="L", color="Black", stock=0),  # out of stock
        ProductVariant(product_id=tshirt.id, size="M", color="White", stock=8),
    ]
    db.add_all(variants)

    jeans = Product(
        name="Slim Fit Jeans",
        description="Slim fit denim.",
        category_id=jeans_cat.id,
        price=1800,
        sale_price=1499,
        sku="JNS-TEST-001",
        image="https://example.com/jeans.jpg",
        active=True,
    )
    db.add(jeans)
    db.flush()
    db.add(ProductVariant(product_id=jeans.id, size="32", color="Blue", stock=15))

    db.commit()
    db.refresh(tshirt)
    db.refresh(jeans)

    return {"tshirt": tshirt, "jeans": jeans, "variants": variants}


@pytest.fixture()
def client(db):
    """FastAPI TestClient wired to the same test db session via dependency override."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def session_id():
    return f"test-session-{uuid.uuid4().hex[:8]}"
