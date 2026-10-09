from typing import Optional, Any, Dict

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    customer_name: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    language: str
    tool_used: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
