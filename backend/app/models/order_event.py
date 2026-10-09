import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class OrderStatusEvent(Base):
    """One row per automatic status change made by the AI fulfillment agent,
    so the admin can see what the AI did and when."""
    __tablename__ = "order_status_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(30), nullable=False, index=True)
    from_status = Column(String(20), nullable=False)
    to_status = Column(String(20), nullable=False)
    actor = Column(String(60), nullable=False, default="AI Fulfillment Agent")
    created_at = Column(DateTime, default=datetime.utcnow)
