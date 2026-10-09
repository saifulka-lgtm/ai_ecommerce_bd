"""
Product/category business logic. This is the ONLY place that reads/writes
product data — both the REST API and the AI tools call through here, so the
AI can never see or report data that didn't come from the database.
"""
import uuid
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product, ProductVariant
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductUpdate, VariantCreate, VariantUpdate


class ProductNotFoundError(Exception):
    pass


class VariantNotFoundError(Exception):
    pass


def list_categories(db: Session) -> List[Category]:
    return db.query(Category).order_by(Category.name).all()


def get_or_create_category(db: Session, name: str) -> Category:
    slug = name.strip().lower().replace(" ", "-")
    category = db.query(Category).filter(func.lower(Category.name) == name.lower()).first()
    if category:
        return category
    category = Category(name=name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _base_query(db: Session):
    return db.query(Product).options(
        joinedload(Product.variants), joinedload(Product.category)
    )


def search_products(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    on_sale: Optional[bool] = None,
    sort: Optional[str] = None,
    active_only: bool = True,
    limit: int = 20,
) -> List[Product]:
    """The single search function behind both `GET /api/products` and the
    `search_products` AI tool. Never returns invented data — only rows that
    exist in PostgreSQL."""
    q = _base_query(db)

    if active_only:
        q = q.filter(Product.active.is_(True))
    if query:
        like = f"%{query.strip()}%"
        q = q.filter(Product.name.ilike(like))
    if category:
        # Prefix match so singular/plural phrasing ("t-shirt" vs "T-Shirts")
        # still resolves, while NOT collapsing distinct categories that
        # happen to share a substring (e.g. "shirt" must not also match
        # "T-Shirts"/"Polo Shirts" — a leading-edge match keeps them apart).
        q = q.join(Category).filter(Category.name.ilike(f"{category.strip()}%"))
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if color:
        q = q.join(ProductVariant).filter(func.lower(ProductVariant.color) == color.strip().lower())
    if size:
        q = q.join(ProductVariant).filter(func.lower(ProductVariant.size) == size.strip().lower())
    if on_sale:
        q = q.filter(Product.sale_price.isnot(None))

    if sort in ("price_asc", "price_desc"):
        # Rank by the price the customer actually pays (sale price when
        # discounted). Done in Python after the query: portable, and avoids
        # Postgres' "SELECT DISTINCT ... ORDER BY expression" restriction.
        products = q.distinct().all()
        products.sort(key=lambda p: float(p.effective_price), reverse=(sort == "price_desc"))
        return products[:limit]

    return q.distinct().order_by(Product.created_at.desc()).limit(limit).all()


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = _base_query(db).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")
    return product


def get_variant(db: Session, variant_id: uuid.UUID) -> ProductVariant:
    variant = (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.product))
        .filter(ProductVariant.id == variant_id)
        .first()
    )
    if not variant:
        raise VariantNotFoundError(f"Variant {variant_id} not found")
    return variant


def find_variant(db: Session, product_id: uuid.UUID, size: str, color: str) -> Optional[ProductVariant]:
    return (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            func.lower(ProductVariant.size) == size.strip().lower(),
            func.lower(ProductVariant.color) == color.strip().lower(),
        )
        .first()
    )


def check_stock(db: Session, variant_id: uuid.UUID, requested_qty: int) -> bool:
    variant = get_variant(db, variant_id)
    return variant.stock >= requested_qty


def low_stock_products(db: Session, threshold: int = 5) -> List[Product]:
    products = _base_query(db).filter(Product.active.is_(True)).all()
    return [p for p in products if p.total_stock <= threshold]


# ---- Admin CRUD ----

def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        price=payload.price,
        sale_price=payload.sale_price,
        sku=payload.sku,
        image=payload.image,
        active=payload.active,
    )
    db.add(product)
    db.flush()

    for v in payload.variants:
        db.add(ProductVariant(product_id=product.id, size=v.size, color=v.color, stock=v.stock))

    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: uuid.UUID, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: uuid.UUID) -> None:
    product = get_product(db, product_id)
    db.delete(product)
    db.commit()


def add_variant(db: Session, product_id: uuid.UUID, payload: VariantCreate) -> ProductVariant:
    get_product(db, product_id)  # raises if missing
    variant = ProductVariant(product_id=product_id, size=payload.size, color=payload.color, stock=payload.stock)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def update_variant(db: Session, variant_id: uuid.UUID, payload: VariantUpdate) -> ProductVariant:
    variant = get_variant(db, variant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


def decrement_stock(db: Session, variant_id: uuid.UUID, quantity: int) -> None:
    variant = get_variant(db, variant_id)
    if variant.stock < quantity:
        raise ValueError("Insufficient stock")
    variant.stock -= quantity
    db.commit()


def to_list_item(product: Product) -> dict:
    """Shape used for product cards (search results, recommendations)."""
    price = float(product.price)
    sale_price = float(product.sale_price) if product.sale_price else None
    # Always computed here from the real price/sale_price — never a number
    # the AI invents. None when the product isn't currently on sale.
    discount_percent = round((1 - sale_price / price) * 100) if sale_price else None
    return {
        "id": str(product.id),
        "name": product.name,
        "category": product.category.name if product.category else "",
        "price": price,
        "sale_price": sale_price,
        "effective_price": float(product.effective_price),
        "discount_percent": discount_percent,
        "image": product.image,
        "sizes": sorted({v.size for v in product.variants}),
        "colors": sorted({v.color for v in product.variants}),
        "total_stock": product.total_stock,
        "in_stock": product.total_stock > 0,
    }
