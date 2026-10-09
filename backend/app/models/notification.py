import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Notification(Base):
    """An alert the AI raises for the admin on its own (e.g. stock running low)."""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(30), nullable=False)       # LOW_STOCK | OUT_OF_STOCK
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
