import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderItemOut(BaseModel):
    product_name: str
    size: str
    color: str
    unit_price: float
    quantity: int
    subtotal: float


class OrderOut(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_name: str
    customer_phone: str
    customer_address: str
    items: List[OrderItemOut]
    subtotal: float
    delivery_charge: float
    discount: float
    total: float
    payment_method: str
    payment_status: str
    order_status: str
    created_at: datetime
    updated_at: datetime


class CreateOrderRequest(BaseModel):
    session_id: str
    customer_name: str = Field(min_length=1)
    customer_phone: str = Field(min_length=6)
    customer_address: str = Field(min_length=3)
    payment_method: str = Field(description="demo_cod | demo_card | demo_mobile")


class UpdateOrderStatusRequest(BaseModel):
    order_status: Optional[str] = None
    payment_status: Optional[str] = None
