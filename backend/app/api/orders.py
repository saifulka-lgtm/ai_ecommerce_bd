import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import order_service, cart_service
from app.schemas.order import CreateOrderRequest, OrderOut, OrderSummary

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut)
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    try:
        order = order_service.create_demo_order(
            db,
            session_id=payload.session_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            payment_method=payload.payment_method,
        )
    except order_service.EmptyCartError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except order_service.InvalidPaymentMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except cart_service.InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order_service.to_out_dict(order)


@router.get("/{order_number}", response_model=OrderOut)
def get_order(order_number: str, phone: str = Query(..., description="Phone used when placing the order"), db: Session = Depends(get_db)):
    try:
        order = order_service.get_order_for_customer(db, order_number, phone)
    except order_service.OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_service.to_out_dict(order)


@router.get("", response_model=list[OrderSummary])
def get_customer_orders(phone: str = Query(...), db: Session = Depends(get_db)):
    # Summary only (no names/addresses/items): a phone number alone is weak proof.
    orders = order_service.get_customer_orders(db, phone)
    return [order_service.to_summary_dict(o) for o in orders]


@router.post("/{order_number}/cancel", response_model=OrderOut)
def cancel_order(order_number: str, phone: str = Query(..., description="Phone used when placing the order"), db: Session = Depends(get_db)):
    try:
        order_service.get_order_for_customer(db, order_number, phone)
        order = order_service.cancel_demo_order(db, order_number)
    except order_service.OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    except order_service.OrderNotCancellableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order_service.to_out_dict(order)
