"""
Every tool function has the signature (args: dict, ctx: ToolContext) -> dict.
ctx carries the DB session plus per-conversation state the tools need to
resolve natural references like "the second one" without the AI ever
inventing an id itself.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_conversation import AIConversation


@dataclass
class ToolContext:
    db: Session
    session_id: str
    conversation: AIConversation
