"""
Seeds the database with realistic demo clothing products for a
Bangladesh-focused store. Run with:

    python seed.py

Safe to re-run: it clears existing catalog data first (not orders/AI logs).
"""
import random

from sqlalchemy import inspect

from app.database import engine, SessionLocal
from app import models
from app.models.category import Category
from app.models.product import Product, ProductVariant

CATEGORIES = ["T-Shirts", "Shirts", "Polo Shirts", "Jeans", "Pants", "Hoodies", "Jackets"]

# Real product photography (via Unsplash), one representative flat-lay /
# product-only shot per category — each picked and checked (via the
# photo's own alt-text metadata) to show only the garment: no person, no
# model, no animal, just the item on a table/hanger/rack/plain background.
CATEGORY_IMAGE_URL = {
    "T-Shirts": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990",
    "Shirts": "https://images.unsplash.com/photo-1602810316693-3667c854239a",
    "Polo Shirts": "https://images.unsplash.com/photo-1671438118097-479e63198629",
    "Jeans": "https://images.unsplash.com/photo-1714143136372-ddaf8b606da7",
    "Pants": "https://images.unsplash.com/photo-1590159983013-d4ff5fc71c1d",
    "Hoodies": "https://images.unsplash.com/photo-1680292783974-a9a336c10366",
    "Jackets": "https://images.unsplash.com/photo-1543076447-215ad9ba6923",
}


def product_image_url(category: str) -> str:
    base = CATEGORY_IMAGE_URL.get(category, CATEGORY_IMAGE_URL["T-Shirts"])
    return f"{base}?w=500&h=625&fit=crop&q=80&auto=format"

SIZES_APPAREL = ["S", "M", "L", "XL"]
SIZES_BOTTOMS = ["30", "32", "34", "36"]

PRODUCTS = [
    # name, category, price, sale_price, sku, colors, sizes, image
    ("Basic Cotton T-Shirt", "T-Shirts", 650, None, "TSH-001", ["Black", "White", "Navy"], SIZES_APPAREL),
    ("Graphic Print T-Shirt", "T-Shirts", 750, 650, "TSH-002", ["Black", "White"], SIZES_APPAREL),
    ("Premium Round-Neck Tee", "T-Shirts", 850, None, "TSH-003", ["Grey", "Maroon", "Black"], SIZES_APPAREL),
    ("V-Neck Cotton Tee", "T-Shirts", 700, None, "TSH-004", ["White", "Blue"], SIZES_APPAREL),
    ("Oversized Streetwear Tee", "T-Shirts", 900, 799, "TSH-005", ["Black", "Olive"], SIZES_APPAREL),
    ("Formal Cotton Shirt", "Shirts", 1450, None, "SHT-001", ["White", "Blue"], SIZES_APPAREL),
    ("Checked Casual Shirt", "Shirts", 1250, 1099, "SHT-002", ["Red", "Navy"], SIZES_APPAREL),
    ("Denim Shirt", "Shirts", 1600, None, "SHT-003", ["Blue"], SIZES_APPAREL),
    ("Linen Summer Shirt", "Shirts", 1350, None, "SHT-004", ["White", "Beige"], SIZES_APPAREL),
    ("Classic Polo Shirt", "Polo Shirts", 950, None, "POL-001", ["Black", "Navy", "White"], SIZES_APPAREL),
    ("Pique Polo Shirt", "Polo Shirts", 1050, 899, "POL-002", ["Red", "Green"], SIZES_APPAREL),
    ("Slim Fit Polo", "Polo Shirts", 1100, None, "POL-003", ["Grey", "Black"], SIZES_APPAREL),
    ("Slim Fit Jeans", "Jeans", 1800, None, "JNS-001", ["Blue", "Black"], SIZES_BOTTOMS),
    ("Regular Fit Jeans", "Jeans", 1650, 1499, "JNS-002", ["Blue"], SIZES_BOTTOMS),
    ("Distressed Denim Jeans", "Jeans", 1950, None, "JNS-003", ["Blue"], SIZES_BOTTOMS),
    ("Chino Pants", "Pants", 1400, None, "PNT-001", ["Beige", "Black", "Navy"], SIZES_BOTTOMS),
    ("Formal Trousers", "Pants", 1550, None, "PNT-002", ["Black", "Grey"], SIZES_BOTTOMS),
    ("Cargo Pants", "Pants", 1700, 1499, "PNT-003", ["Olive", "Black"], SIZES_BOTTOMS),
    ("Pullover Hoodie", "Hoodies", 1650, None, "HOD-001", ["Black", "Grey"], SIZES_APPAREL),
    ("Zip-Up Hoodie", "Hoodies", 1800, 1599, "HOD-002", ["Navy", "Maroon"], SIZES_APPAREL),
    ("Denim Jacket", "Jackets", 2400, None, "JKT-001", ["Blue"], SIZES_APPAREL),
    ("Bomber Jacket", "Jackets", 2800, 2499, "JKT-002", ["Black", "Olive"], SIZES_APPAREL),
    ("Windbreaker Jacket", "Jackets", 2200, None, "JKT-003", ["Navy", "Black"], SIZES_APPAREL),
]


def run():
    # Tables come from Alembic migrations, not from here.
    if "products" not in inspect(engine).get_table_names():
        raise SystemExit("Database tables are missing. Run first:  alembic upgrade head")
    db = SessionLocal()
    try:
        print("Clearing existing catalog data...")
        db.query(ProductVariant).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.commit()

        categories = {}
        for name in CATEGORIES:
            cat = Category(name=name, slug=name.lower().replace(" ", "-"))
            db.add(cat)
            categories[name] = cat
        db.commit()

        print("Creating products...")
        for name, cat_name, price, sale_price, sku, colors, sizes in PRODUCTS:
            product = Product(
                name=name,
                description=f"{name} — comfortable everyday wear, designed for the Bangladesh climate.",
                category_id=categories[cat_name].id,
                price=price,
                sale_price=sale_price,
                sku=sku,
                image=product_image_url(cat_name),
                active=True,
            )
            db.add(product)
            db.flush()

            for color in colors:
                for size in sizes:
                    stock = random.choice([0, 3, 5, 8, 12, 20, 30])
                    db.add(ProductVariant(product_id=product.id, size=size, color=color, stock=stock))

        db.commit()
        total_products = db.query(Product).count()
        total_variants = db.query(ProductVariant).count()
        print(f"Done. Seeded {total_products} products with {total_variants} variants across {len(CATEGORIES)} categories.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
