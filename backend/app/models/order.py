import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "PENDING"
    confirmed = "CONFIRMED"
    shipped = "SHIPPED"
    delivered = "DELIVERED"
    cancelled = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(30), unique=True, nullable=False, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(150), nullable=False)
    customer_phone = Column(String(30), nullable=False)
    customer_address = Column(String(500), nullable=False)

    subtotal = Column(Numeric(10, 2), nullable=False)
    delivery_charge = Column(Numeric(10, 2), nullable=False, default=0)
    discount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False)

    payment_method = Column(String(30), nullable=False)  # demo_cod | demo_card | demo_mobile
    payment_status = Column(String(30), nullable=False, default="PENDING")  # PENDING | DEMO_SUCCESS | DEMO_FAILED
    order_status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False)

    # Snapshot fields so historical orders remain accurate even if the product changes later
    product_name = Column(String(200), nullable=False)
    size = Column(String(20), nullable=False)
    color = Column(String(50), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
