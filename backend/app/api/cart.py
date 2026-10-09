from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import cart_service, product_service
from app.schemas.cart import AddToCartRequest, UpdateCartItemRequest, CartOut

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/{session_id}", response_model=CartOut)
def get_cart(session_id: str, db: Session = Depends(get_db)):
    return cart_service.calculate_cart_total(db, session_id)


@router.post("/add", response_model=CartOut)
def add_to_cart(payload: AddToCartRequest, db: Session = Depends(get_db)):
    try:
        cart_service.add_to_cart(db, payload.session_id, payload.variant_id, payload.quantity)
    except product_service.VariantNotFoundError:
        raise HTTPException(status_code=404, detail="Product variant not found")
    except cart_service.InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return cart_service.calculate_cart_total(db, payload.session_id)


@router.put("/{session_id}/items/{variant_id}", response_model=CartOut)
def update_quantity(session_id: str, variant_id: str, payload: UpdateCartItemRequest, db: Session = Depends(get_db)):
    try:
        cart_service.update_cart_quantity(db, session_id, variant_id, payload.quantity)
    except cart_service.CartItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not in cart")
    except cart_service.InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return cart_service.calculate_cart_total(db, session_id)


@router.delete("/{session_id}/items/{variant_id}", response_model=CartOut)
def remove_item(session_id: str, variant_id: str, db: Session = Depends(get_db)):
    try:
        cart_service.remove_from_cart(db, session_id, variant_id)
    except cart_service.CartItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return cart_service.calculate_cart_total(db, session_id)
