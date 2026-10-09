"""
Cart business logic — single source of truth for both the REST API and the
AI tools. Totals and stock checks are always computed here on the backend,
never trusted from the AI or the client.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.cart import Cart, CartItem
from app.models.product import ProductVariant
from app.services import product_service
from app.services.product_service import VariantNotFoundError

settings = get_settings()


class CartItemNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


def get_or_create_cart(db: Session, session_id: str) -> Cart:
    cart = db.query(Cart).filter(Cart.session_id == session_id).first()
    if cart:
        return cart
    cart = Cart(session_id=session_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def _loaded_cart(db: Session, session_id: str) -> Cart:
    cart = get_or_create_cart(db, session_id)
    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.variant).joinedload(ProductVariant.product))
        .filter(Cart.id == cart.id)
        .first()
    )


def add_to_cart(db: Session, session_id: str, variant_id: uuid.UUID, quantity: int) -> Cart:
    variant = product_service.get_variant(db, variant_id)  # raises VariantNotFoundError
    if variant.stock < quantity:
        raise InsufficientStockError(
            f"Only {variant.stock} in stock for {variant.product.name} ({variant.size}/{variant.color})"
        )

    cart = get_or_create_cart(db, session_id)
    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
        .first()
    )
    if existing:
        new_qty = existing.quantity + quantity
        if variant.stock < new_qty:
            raise InsufficientStockError(f"Only {variant.stock} in stock")
        existing.quantity = new_qty
    else:
        db.add(CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity))

    db.commit()
    return _loaded_cart(db, session_id)


def remove_from_cart(db: Session, session_id: str, variant_id: uuid.UUID) -> Cart:
    cart = get_or_create_cart(db, session_id)
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
        .first()
    )
    if not item:
        raise CartItemNotFoundError("Item not in cart")
    db.delete(item)
    db.commit()
    return _loaded_cart(db, session_id)


def update_cart_quantity(db: Session, session_id: str, variant_id: uuid.UUID, quantity: int) -> Cart:
    cart = get_or_create_cart(db, session_id)
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
        .first()
    )
    if not item:
        raise CartItemNotFoundError("Item not in cart")

    variant = product_service.get_variant(db, variant_id)
    if variant.stock < quantity:
        raise InsufficientStockError(f"Only {variant.stock} in stock")

    item.quantity = quantity
    db.commit()
    return _loaded_cart(db, session_id)


def get_cart(db: Session, session_id: str) -> Cart:
    return _loaded_cart(db, session_id)


def calculate_cart_total(db: Session, session_id: str) -> dict:
    cart = _loaded_cart(db, session_id)
    subtotal = 0.0
    items = []
    for item in cart.items:
        product = item.variant.product
        unit_price = float(product.effective_price)
        line_subtotal = unit_price * item.quantity
        subtotal += line_subtotal
        items.append(
            {
                "variant_id": str(item.variant_id),
                "product_id": str(product.id),
                "product_name": product.name,
                "image": product.image,
                "size": item.variant.size,
                "color": item.variant.color,
                "unit_price": unit_price,
                "quantity": item.quantity,
                "subtotal": round(line_subtotal, 2),
            }
        )

    delivery_charge = 0.0 if (subtotal >= settings.free_delivery_threshold or subtotal == 0) else settings.demo_delivery_charge
    total = subtotal + delivery_charge

    return {
        "session_id": session_id,
        "items": items,
        "subtotal": round(subtotal, 2),
        "delivery_charge": round(delivery_charge, 2),
        "total": round(total, 2),
        "item_count": sum(i["quantity"] for i in items),
    }


def clear_cart(db: Session, session_id: str) -> None:
    cart = get_or_create_cart(db, session_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
