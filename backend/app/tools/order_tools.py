from typing import Any, Dict

from app.services import order_service, cart_service, conversation_service
from app.tools.context import ToolContext
from app.tools.product_tools import _ok, _err

REQUIRED_ORDER_FIELDS = ["customer_name", "customer_phone", "customer_address", "payment_method"]


def create_demo_order(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    missing = [f for f in REQUIRED_ORDER_FIELDS if not args.get(f)]
    if missing:
        return _err(
            "Missing information needed to place the order.",
            data={"missing_fields": missing},
        )

    try:
        order = order_service.create_demo_order(
            ctx.db,
            session_id=ctx.session_id,
            customer_name=args["customer_name"],
            customer_phone=args["customer_phone"],
            customer_address=args["customer_address"],
            payment_method=args["payment_method"],
        )
    except order_service.EmptyCartError as e:
        return _err(str(e))
    except order_service.InvalidPaymentMethodError as e:
        return _err(str(e))
    except cart_service.InsufficientStockError as e:
        return _err(str(e))

    return _ok(order_service.to_out_dict(order))


def get_order(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    order_number = args.get("order_number") or conversation_service.get_last_order_number(ctx.db, ctx.conversation)
    if not order_number:
        return _err("Which order number would you like to check?")

    try:
        order = order_service.get_order_by_number(ctx.db, order_number)
    except order_service.OrderNotFoundError:
        return _err(f"No order found with number {order_number}.")

    return _ok(order_service.to_out_dict(order))


def get_customer_orders(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    phone = args.get("customer_phone")
    if not phone:
        return _err("Could you share the phone number you used to order?")

    orders = order_service.get_customer_orders(ctx.db, phone)
    return _ok({"orders": [order_service.to_out_dict(o) for o in orders], "count": len(orders)})


def cancel_demo_order(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    order_number = args.get("order_number") or conversation_service.get_last_order_number(ctx.db, ctx.conversation)
    if not order_number:
        return _err("Which order number would you like to cancel?")

    try:
        order = order_service.cancel_demo_order(ctx.db, order_number)
    except order_service.OrderNotFoundError:
        return _err(f"No order found with number {order_number}.")
    except order_service.OrderNotCancellableError as e:
        return _err(str(e))

    return _ok(order_service.to_out_dict(order))


def check_order_status(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    order_number = args.get("order_number") or conversation_service.get_last_order_number(ctx.db, ctx.conversation)
    if not order_number:
        return _err("Which order number would you like the status of?")

    try:
        status = order_service.check_order_status(ctx.db, order_number)
    except order_service.OrderNotFoundError:
        return _err(f"No order found with number {order_number}.")

    return _ok(status)
