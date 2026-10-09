import uuid
from typing import List

from pydantic import BaseModel, Field


class CartItemOut(BaseModel):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    image: str | None = None
    size: str
    color: str
    unit_price: float
    quantity: int
    subtotal: float


class CartOut(BaseModel):
    session_id: str
    items: List[CartItemOut]
    subtotal: float
    delivery_charge: float
    total: float
    item_count: int


class AddToCartRequest(BaseModel):
    session_id: str
    variant_id: uuid.UUID
    quantity: int = Field(default=1, gt=0)


class UpdateCartItemRequest(BaseModel):
    session_id: str
    quantity: int = Field(gt=0)


class RemoveFromCartRequest(BaseModel):
    session_id: str
