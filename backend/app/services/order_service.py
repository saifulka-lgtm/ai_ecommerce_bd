"""
Order + demo payment business logic. Totals are always recomputed on the
backend from the cart at order-creation time — the AI/client-supplied total
is never trusted. Stock is verified and decremented atomically here.
"""
import uuid
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment
from app.services import cart_service, product_service
from app.utils.generators import generate_order_number, generate_transaction_ref

VALID_PAYMENT_METHODS = {"demo_cod", "demo_card", "demo_mobile"}
CANCELLABLE_STATUSES = {OrderStatus.pending, OrderStatus.confirmed}


class EmptyCartError(Exception):
    pass


class InvalidPaymentMethodError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderNotCancellableError(Exception):
    pass


def _loaded(db: Session, order: Order) -> Order:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.id == order.id)
        .first()
    )


def create_demo_order(
    db: Session,
    session_id: str,
    customer_name: str,
    customer_phone: str,
    customer_address: str,
    payment_method: str,
) -> Order:
    if payment_method not in VALID_PAYMENT_METHODS:
        raise InvalidPaymentMethodError(f"Unknown demo payment method: {payment_method}")

    totals = cart_service.calculate_cart_total(db, session_id)
    if not totals["items"]:
        raise EmptyCartError("Cannot create an order from an empty cart")

    # Re-verify stock for every line right before committing the order.
    cart = cart_service.get_or_create_cart(db, session_id)
    for item in cart.items:
        if item.variant.stock < item.quantity:
            raise cart_service.InsufficientStockError(
                f"Only {item.variant.stock} left of {item.variant.product.name} "
                f"({item.variant.size}/{item.variant.color})"
            )

    order = Order(
        order_number=generate_order_number(),
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        subtotal=totals["subtotal"],
        delivery_charge=totals["delivery_charge"],
        discount=0,
        total=totals["total"],
        payment_method=payment_method,
        payment_status="PENDING",
        order_status=OrderStatus.pending,
    )
    db.add(order)
    db.flush()

    for item in cart.items:
        product = item.variant.product
        unit_price = float(product.effective_price)
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                variant_id=item.variant_id,
                product_name=product.name,
                size=item.variant.size,
                color=item.variant.color,
                unit_price=unit_price,
                quantity=item.quantity,
                subtotal=round(unit_price * item.quantity, 2),
            )
        )
        # Decrement stock now that the order is committed to.
        item.variant.stock -= item.quantity

    # Simulate the demo payment — always succeeds, no real money moves.
    payment = Payment(
        order_id=order.id,
        method=payment_method,
        status="DEMO_SUCCESS",
        amount=totals["total"],
        transaction_ref=generate_transaction_ref(),
    )
    db.add(payment)
    order.payment_status = "DEMO_SUCCESS"

    db.commit()
    db.refresh(order)

    cart_service.clear_cart(db, session_id)

    return _loaded(db, order)


def get_order_by_number(db: Session, order_number: str) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.order_number == order_number)
        .first()
    )
    if not order:
        raise OrderNotFoundError(f"Order {order_number} not found")
    return order


def get_order_by_id(db: Session, order_id: uuid.UUID) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise OrderNotFoundError(f"Order {order_id} not found")
    return order


def get_customer_orders(db: Session, customer_phone: str) -> List[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.customer_phone == customer_phone)
        .order_by(Order.created_at.desc())
        .all()
    )


def check_order_status(db: Session, order_number: str) -> dict:
    order = get_order_by_number(db, order_number)
    return {
        "order_number": order.order_number,
        "order_status": order.order_status.value,
        "payment_status": order.payment_status,
        "total": float(order.total),
    }


def cancel_demo_order(db: Session, order_number: str) -> Order:
    order = get_order_by_number(db, order_number)
    if order.order_status not in CANCELLABLE_STATUSES:
        raise OrderNotCancellableError(
            f"Order {order_number} is {order.order_status.value} and can no longer be cancelled"
        )

    # Restock items
    for item in order.items:
        try:
            variant = product_service.get_variant(db, item.variant_id)
            variant.stock += item.quantity
        except product_service.VariantNotFoundError:
            pass  # variant may have been deleted since

    order.order_status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return _loaded(db, order)


def list_all_orders(db: Session, status: Optional[str] = None) -> List[Order]:
    q = db.query(Order).options(joinedload(Order.items), joinedload(Order.payment))
    if status:
        q = q.filter(Order.order_status == status)
    return q.order_by(Order.created_at.desc()).all()


def update_order_status(db: Session, order_id: uuid.UUID, order_status: Optional[str], payment_status: Optional[str]) -> Order:
    order = get_order_by_id(db, order_id)
    if order_status:
        order.order_status = OrderStatus(order_status)
    if payment_status:
        order.payment_status = payment_status
    db.commit()
    db.refresh(order)
    return _loaded(db, order)


def to_out_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_address": order.customer_address,
        "items": [
            {
                "product_name": i.product_name,
                "size": i.size,
                "color": i.color,
                "unit_price": float(i.unit_price),
                "quantity": i.quantity,
                "subtotal": float(i.subtotal),
            }
            for i in order.items
        ],
        "subtotal": float(order.subtotal),
        "delivery_charge": float(order.delivery_charge),
        "discount": float(order.discount),
        "total": float(order.total),
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "order_status": order.order_status.value,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }
