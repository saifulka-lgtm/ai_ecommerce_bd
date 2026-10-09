import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class StockMovement(Base):
    """Append-only history of every stock change (sale, cancellation restock),
    so the admin can track why a quantity moved. Product details are copied in
    so the history survives a product being edited or deleted."""
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name = Column(String(200), nullable=False)
    size = Column(String(20), nullable=False)
    color = Column(String(50), nullable=False)
    change = Column(Integer, nullable=False)       # negative = stock out, positive = stock in
    stock_after = Column(Integer, nullable=False)
    reason = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
