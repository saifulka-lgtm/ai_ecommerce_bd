"""
The AI Agent — the orchestration layer described in the architecture:

    Customer -> React UI -> FastAPI -> AI Agent -> Intent understanding ->
    Tool selection -> Backend Tool -> Database -> Tool Result -> AI Response -> Customer

This module never talks to the database directly for business data — it
only: (1) asks the active AIProvider to decide what to do, (2) executes at
most one tool call through the tool registry, (3) logs the call, and
(4) asks the provider to phrase the result. It is provider-agnostic by
construction.
"""
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.ai.constants import ORDER_PENDING_MARKER
from app.models.ai_conversation import AIToolLog
from app.services import conversation_service
from app.tools.context import ToolContext
from app.tools.registry import TOOL_SPECS, execute_tool


def _build_pending_order_hint(db: Session, conversation) -> Optional[str]:
    """If the customer's last tool call was an incomplete create_demo_order,
    tell the provider so it keeps collecting order info this turn even if
    the new message doesn't repeat an 'order' keyword."""
    last_log = (
        db.query(AIToolLog)
        .filter(AIToolLog.conversation_id == conversation.id)
        .order_by(AIToolLog.created_at.desc())
        .first()
    )
    if not last_log or last_log.tool_name != "create_demo_order":
        return None
    if last_log.success:
        return None
    missing = (last_log.tool_result or {}).get("missing_fields") or (last_log.tool_result or {}).get("data", {}).get("missing_fields")
    if not missing:
        return None
    return f"{ORDER_PENDING_MARKER} still need: {', '.join(missing)}"


def _structured_data_for(tool_name: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not result.get("success"):
        return None
    data = result.get("data") or {}

    if "products" in data:
        return {"products": data["products"]}
    if "product" in data:
        return {"products": [data["product"]]}
    if "order_number" in data:
        return {"order_number": data["order_number"], "order": data}
    if "orders" in data:
        return {"orders": data["orders"]}
    if "items" in data:  # cart shape
        return data
    return data or None


def handle_message(db: Session, session_id: str, message: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
    provider = get_ai_provider()
    conversation = conversation_service.get_or_create_conversation(db, session_id, customer_name)

    prior_messages = conversation_service.get_recent_messages(db, conversation, limit=12)
    history = [{"role": m.role, "content": m.content} for m in prior_messages]

    pending_hint = _build_pending_order_hint(db, conversation)
    if pending_hint:
        history.append({"role": "system", "content": pending_hint})

    conversation_service.add_message(db, conversation, "user", message)

    decision = provider.decide_action(message, history, TOOL_SPECS)

    tool_used = None
    structured_data = None

    if decision.tool_name:
        ctx = ToolContext(db=db, session_id=session_id, conversation=conversation)
        start = time.time()
        result = execute_tool(decision.tool_name, decision.tool_arguments, ctx)
        elapsed_ms = int((time.time() - start) * 1000)

        db.add(AIToolLog(
            conversation_id=conversation.id,
            customer_message=message,
            tool_name=decision.tool_name,
            tool_arguments=decision.tool_arguments,
            tool_result=result,
            execution_time_ms=elapsed_ms,
            success=bool(result.get("success")),
            error_message=None if result.get("success") else result.get("error"),
        ))
        db.commit()

        reply_text = provider.generate_reply(
            message, decision.language, decision.tool_name, decision.tool_arguments, result
        )
        tool_used = decision.tool_name
        structured_data = _structured_data_for(decision.tool_name, result)
    else:
        reply_text = decision.direct_reply or "Sorry, could you rephrase that?"

    conversation_service.add_message(
        db, conversation, "assistant", reply_text, language=decision.language, structured_data=structured_data
    )

    return {
        "reply": reply_text,
        "language": decision.language,
        "tool_used": tool_used,
        "data": structured_data,
    }
