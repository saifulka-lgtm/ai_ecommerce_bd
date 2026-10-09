"""
Admin order assistant — lets a logged-in admin change order statuses by
typing a sentence ("DEMO-1234 শিপ করো", "mark DEMO-1234 as delivered").

Deliberately separate from the customer chat: it is only reachable through
an endpoint guarded by require_admin, so ordinary customers can never change
an order's status. It works on real orders through order_service — it never
invents order data.
"""
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai import nlu
from app.models.order import OrderStatus
from app.services import order_service

ORDER_NO_RE = re.compile(r"DEMO-\d{4}")

# Checked in this order; first match wins.
STATUS_KEYWORDS = [
    ("CANCELLED", ["cancel", "বাতিল"]),
    ("DELIVERED", ["deliver", "ডেলিভার", "পৌঁছ", "পৌছ"]),
    ("SHIPPED", ["ship", "শিপ", "পাঠিয়ে", "পাঠানো"]),
    ("CONFIRMED", ["confirm", "কনফার্ম"]),
    ("PENDING", ["pending", "পেন্ডিং"]),
]

STATUS_BN = {
    "PENDING": "পেন্ডিং",
    "CONFIRMED": "কনফার্মড",
    "SHIPPED": "শিপড",
    "DELIVERED": "ডেলিভারড",
    "CANCELLED": "বাতিল",
}

# Allowed forward moves. DELIVERED and CANCELLED are final.
ALLOWED = {
    "PENDING": {"CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"},
    "CONFIRMED": {"SHIPPED", "DELIVERED", "CANCELLED"},
    "SHIPPED": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}

HELP = {
    "en": "Tell me an order number and what to do, e.g. \"DEMO-1234 ship\", \"mark DEMO-1234 as delivered\", or \"show confirmed orders\".",
    "bn": "অর্ডার নম্বর আর কী করতে হবে লিখুন, যেমন \"DEMO-1234 শিপ করো\", \"DEMO-1234 ডেলিভার্ড করো\" বা \"কনফার্মড অর্ডার দেখাও\"।",
}


def extract_target_status(text: str) -> Optional[str]:
    lower = text.lower()
    for status, words in STATUS_KEYWORDS:
        if any(w in lower for w in words):
            return status
    return None


def _label(status: str, language: str) -> str:
    return STATUS_BN.get(status, status) if language == "bn" else status


def handle_admin_message(db: Session, message: str) -> Dict[str, Any]:
    language = nlu.detect_language(message)
    numbers: List[str] = list(dict.fromkeys(ORDER_NO_RE.findall(message.upper())))
    target = extract_target_status(message)

    # 1) Update one or more named orders.
    if numbers and target:
        lines: List[str] = []
        orders: List[Dict[str, Any]] = []
        for number in numbers:
            try:
                order = order_service.get_order_by_number(db, number)
            except order_service.OrderNotFoundError:
                lines.append(f"{number}: পাওয়া যায়নি।" if language == "bn" else f"{number}: not found.")
                continue
            current = order.order_status.value
            if current == target:
                lines.append(
                    f"{number}: আগে থেকেই {_label(current, language)}।" if language == "bn"
                    else f"{number}: already {current}."
                )
            elif target not in ALLOWED[current]:
                lines.append(
                    f"{number}: {_label(current, language)} অবস্থা থেকে {_label(target, language)} করা যায় না।" if language == "bn"
                    else f"{number}: can't change from {current} to {target}."
                )
            else:
                order = order_service.update_order_status(db, order.id, target, None)
                lines.append(
                    f"{number}: {_label(current, language)} → {_label(target, language)} করা হয়েছে।" if language == "bn"
                    else f"{number}: {current} → {target}."
                )
            orders.append(order_service.to_out_dict(order))
        return {"reply": "\n".join(lines), "language": language, "orders": orders, "changed": any("→" in l for l in lines)}

    # 2) Named order(s) with no action -> show them.
    if numbers:
        found, lines = [], []
        for number in numbers:
            try:
                o = order_service.get_order_by_number(db, number)
            except order_service.OrderNotFoundError:
                lines.append(f"{number}: পাওয়া যায়নি।" if language == "bn" else f"{number}: not found.")
                continue
            found.append(order_service.to_out_dict(o))
            lines.append(
                f"{o.order_number} — {o.customer_name}, ৳{float(o.total):.0f}, {_label(o.order_status.value, language)}"
            )
        return {"reply": "\n".join(lines), "language": language, "orders": found, "changed": False}

    # 3) A status word and no order number -> list orders in that status.
    if target:
        orders_found = order_service.list_all_orders(db, status=target)
        if not orders_found:
            reply = f"কোনো {_label(target, 'bn')} অর্ডার নেই।" if language == "bn" else f"No {target} orders."
        else:
            head = f"{len(orders_found)}টি {_label(target, 'bn')} অর্ডার:" if language == "bn" else f"{len(orders_found)} {target} order(s):"
            body = [f"• {o.order_number} — {o.customer_name}, ৳{float(o.total):.0f}" for o in orders_found[:10]]
            reply = "\n".join([head] + body)
        return {"reply": reply, "language": language, "orders": [order_service.to_out_dict(o) for o in orders_found[:10]], "changed": False}

    return {"reply": HELP[language], "language": language, "orders": [], "changed": False}
