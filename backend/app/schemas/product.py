import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str


class CategoryCreate(BaseModel):
    name: str
    slug: str


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    size: str
    color: str
    stock: int


class VariantCreate(BaseModel):
    size: str
    color: str
    stock: int = 0


class VariantUpdate(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: CategoryOut
    price: float
    sale_price: Optional[float] = None
    sku: str
    image: Optional[str] = None
    active: bool
    variants: List[VariantOut] = []
    created_at: datetime
    updated_at: datetime

    @property
    def effective_price(self) -> float:
        return self.sale_price if self.sale_price else self.price


class ProductListItem(BaseModel):
    """Lighter-weight shape used for search results / product cards."""
    id: uuid.UUID
    name: str
    category: str
    price: float
    sale_price: Optional[float] = None
    image: Optional[str] = None
    sizes: List[str]
    colors: List[str]
    total_stock: int
    in_stock: bool


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: uuid.UUID
    price: float = Field(gt=0)
    sale_price: Optional[float] = Field(default=None, ge=0)
    sku: str
    image: Optional[str] = None
    active: bool = True
    variants: List[VariantCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    sku: Optional[str] = None
    image: Optional[str] = None
    active: Optional[bool] = None
