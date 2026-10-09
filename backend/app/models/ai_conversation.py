import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    customer_name = Column(String(150), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")
    tool_logs = relationship("AIToolLog", back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id"), nullable=False)

    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=True)  # bn | en

    # For assistant messages that returned structured data (product cards, cart, order).
    # none_as_null=True is required so a Python None is stored as real SQL NULL
    # instead of the JSON scalar 'null' (which "IS NOT NULL" would still match).
    structured_data = Column(JSON(none_as_null=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("AIConversation", back_populates="messages")


class AIToolLog(Base):
    __tablename__ = "ai_tool_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id"), nullable=False)

    customer_message = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_arguments = Column(JSON, nullable=True)
    tool_result = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("AIConversation", back_populates="tool_logs")
