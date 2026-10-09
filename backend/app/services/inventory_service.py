"""
Inventory tracking for the admin. Everything is read straight from
product_variants (the real stock) and stock_movements (the history).
The admin only tracks; stock changes through orders and cancellations.
"""
from typing import List

from sqlalchemy.orm import Session

from app.models.product import Product, ProductVariant
from app.models.notification import Notification
from app.models.stock_movement import StockMovement
from app.services import product_service

LOW_STOCK_THRESHOLD = 5


def variant_status(stock: int) -> str:
    if stock <= 0:
        return "OUT_OF_STOCK"
    if stock <= LOW_STOCK_THRESHOLD:
        return "LOW"
    return "OK"


def log_movement(db: Session, variant: ProductVariant, change: int, reason: str) -> None:
    """Call right AFTER variant.stock has been changed (same transaction)."""
    db.add(StockMovement(
        product_name=variant.product.name,
        size=variant.size,
        color=variant.color,
        change=change,
        stock_after=variant.stock,
        reason=reason,
    ))
    _raise_stock_alert(db, variant, previous_stock=variant.stock - change)


def _raise_stock_alert(db: Session, variant: ProductVariant, previous_stock: int) -> None:
    """The AI notifies the admin on its own, once, when a variant FIRST drops
    to low stock or runs out - not on every further sale."""
    now = variant.stock
    name = f"{variant.product.name} ({variant.size}/{variant.color})"
    if now <= 0 < previous_stock:
        db.add(Notification(
            type="OUT_OF_STOCK",
            title="স্টক শেষ",
            message=f"{name} — স্টক শেষ হয়ে গেছে। দ্রুত রিস্টক করা দরকার।",
        ))
    elif 0 < now <= LOW_STOCK_THRESHOLD < previous_stock:
        db.add(Notification(
            type="LOW_STOCK",
            title="স্টক কমে গেছে",
            message=f"{name} — স্টক কমে মাত্র {now} পিস আছে।",
        ))


def list_notifications(db: Session, limit: int = 30) -> dict:
    rows = db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
    unread = db.query(Notification).filter(Notification.is_read.is_(False)).count()
    return {
        "unread_count": unread,
        "items": [
            {
                "id": str(r.id),
                "type": r.type,
                "title": r.title,
                "message": r.message,
                "is_read": r.is_read,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


def mark_all_read(db: Session) -> int:
    n = db.query(Notification).filter(Notification.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return n


def inventory_overview(db: Session) -> dict:
    products = product_service.search_products(db, active_only=False, limit=1000)
    items: List[dict] = []
    total_units = out_variants = low_variants = 0

    for p in sorted(products, key=lambda x: x.name):
        variants = []
        for v in sorted(p.variants, key=lambda x: (x.color, x.size)):
            status = variant_status(v.stock)
            total_units += v.stock
            out_variants += status == "OUT_OF_STOCK"
            low_variants += status == "LOW"
            variants.append({"size": v.size, "color": v.color, "stock": v.stock, "status": status})
        statuses = {v["status"] for v in variants}
        overall = "OUT_OF_STOCK" if variants and statuses == {"OUT_OF_STOCK"} else (
            "LOW" if ("LOW" in statuses or "OUT_OF_STOCK" in statuses) else "OK"
        )
        items.append({
            "product_id": str(p.id),
            "name": p.name,
            "category": p.category.name if p.category else "",
            "sku": p.sku,
            "active": p.active,
            "total_stock": p.total_stock,
            "status": overall,
            "variants": variants,
        })

    return {
        "summary": {
            "total_products": len(items),
            "total_units": total_units,
            "low_stock_variants": low_variants,
            "out_of_stock_variants": out_variants,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        },
        "products": items,
    }


def list_movements(db: Session, limit: int = 30) -> List[dict]:
    rows = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "product_name": r.product_name,
            "size": r.size,
            "color": r.color,
            "change": r.change,
            "stock_after": r.stock_after,
            "reason": r.reason,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
