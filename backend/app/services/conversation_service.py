"""
AI conversation memory. Stores every customer/assistant message and, for
assistant messages that returned a product list, the ordered list of
product ids that were shown — this is what lets the agent resolve
"the second one" / "দ্বিতীয়টা" without re-asking the customer.
"""
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.ai_conversation import AIConversation, AIMessage


def get_or_create_conversation(db: Session, session_id: str, customer_name: Optional[str] = None) -> AIConversation:
    convo = db.query(AIConversation).filter(AIConversation.session_id == session_id).first()
    if convo:
        if customer_name and not convo.customer_name:
            convo.customer_name = customer_name
            db.commit()
        return convo
    convo = AIConversation(session_id=session_id, customer_name=customer_name)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def add_message(
    db: Session,
    conversation: AIConversation,
    role: str,
    content: str,
    language: Optional[str] = None,
    structured_data: Optional[Dict[str, Any]] = None,
) -> AIMessage:
    msg = AIMessage(
        conversation_id=conversation.id,
        role=role,
        content=content,
        detected_language=language,
        structured_data=structured_data,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(db: Session, conversation: AIConversation, limit: int = 10) -> List[AIMessage]:
    messages = (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation.id)
        .order_by(AIMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


def get_last_shown_products(db: Session, conversation: AIConversation) -> List[Dict[str, Any]]:
    """Most recent assistant message that carried a product list, so ordinal
    references ("the first one", "প্রথমটা") can be resolved."""
    msg = (
        db.query(AIMessage)
        .filter(
            AIMessage.conversation_id == conversation.id,
            AIMessage.role == "assistant",
            AIMessage.structured_data.isnot(None),
        )
        .order_by(AIMessage.created_at.desc())
        .first()
    )
    if not msg or not msg.structured_data:
        return []
    return msg.structured_data.get("products", [])


def get_last_order_number(db: Session, conversation: AIConversation) -> Optional[str]:
    msg = (
        db.query(AIMessage)
        .filter(
            AIMessage.conversation_id == conversation.id,
            AIMessage.role == "assistant",
            AIMessage.structured_data.isnot(None),
        )
        .order_by(AIMessage.created_at.desc())
        .all()
    )
    for m in msg:
        if m.structured_data and m.structured_data.get("order_number"):
            return m.structured_data["order_number"]
    return None
