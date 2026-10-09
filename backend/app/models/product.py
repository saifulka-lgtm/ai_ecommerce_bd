import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=True)
    sku = Column(String(50), unique=True, nullable=False)
    # Text, not String(N): product images are data: URI SVGs (self-drawn
    # icons, no external photos), which run well past a typical URL length.
    image = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    @property
    def effective_price(self):
        return self.sale_price if self.sale_price else self.price

    @property
    def total_stock(self) -> int:
        return sum(v.stock for v in self.variants)


class ProductVariant(Base):
    """A specific size/color combination of a product, with its own stock."""

    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    size = Column(String(20), nullable=False)
    color = Column(String(50), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="variants")
