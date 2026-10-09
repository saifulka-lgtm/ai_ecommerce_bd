"""
AI fulfillment agent — moves orders through PENDING -> CONFIRMED -> SHIPPED
-> DELIVERED automatically, so nobody has to change statuses by hand.

It is a deterministic, time-based rule engine (demo timings, configurable in
.env), not an LLM: it only ever touches real orders in PostgreSQL, only moves
them forward, and records every move in order_status_events. CANCELLED and
DELIVERED orders are final and never touched.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.order_event import OrderStatusEvent

ACTOR = "AI Fulfillment Agent"


def _steps(confirm_after: int, ship_after: int, deliver_after: int) -> Dict[OrderStatus, tuple]:
    # current status -> (next status, seconds the order must sit in the current status)
    return {
        OrderStatus.pending: (OrderStatus.confirmed, confirm_after),
        OrderStatus.confirmed: (OrderStatus.shipped, ship_after),
        OrderStatus.shipped: (OrderStatus.delivered, deliver_after),
    }


def advance_orders(
    db: Session,
    confirm_after: int,
    ship_after: int,
    deliver_after: int,
    now: Optional[datetime] = None,
) -> List[dict]:
    """Advance every order that has waited long enough in its current status
    by ONE step. Returns the list of changes made."""
    now = now or datetime.utcnow()
    steps = _steps(confirm_after, ship_after, deliver_after)
    changes: List[dict] = []

    orders = db.query(Order).filter(Order.order_status.in_(list(steps.keys()))).all()
    for order in orders:
        next_status, wait_seconds = steps[order.order_status]
        since = order.updated_at or order.created_at
        if now - since < timedelta(seconds=wait_seconds):
            continue
        old = order.order_status
        order.order_status = next_status
        order.updated_at = now
        db.add(OrderStatusEvent(
            order_number=order.order_number,
            from_status=old.value,
            to_status=next_status.value,
            actor=ACTOR,
        ))
        changes.append({"order_number": order.order_number, "from": old.value, "to": next_status.value})

    if changes:
        db.commit()
    return changes


def list_events(db: Session, limit: int = 30) -> List[dict]:
    rows = db.query(OrderStatusEvent).order_by(OrderStatusEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "order_number": r.order_number,
            "from_status": r.from_status,
            "to_status": r.to_status,
            "actor": r.actor,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
