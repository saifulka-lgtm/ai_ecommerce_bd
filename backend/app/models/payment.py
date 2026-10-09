import uuid
from datetime import datetime

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Payment(Base):
    """A simulated payment record. No real money or real payment gateway is ever involved."""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False)

    method = Column(String(30), nullable=False)  # demo_cod | demo_card | demo_mobile
    status = Column(String(30), nullable=False, default="DEMO_SUCCESS")
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_ref = Column(String(50), nullable=False)  # e.g. DEMO-TXN-XXXXXX

    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")
