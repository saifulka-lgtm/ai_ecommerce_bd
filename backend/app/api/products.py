import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import product_service
from app.schemas.product import ProductOut, ProductListItem, CategoryOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return product_service.list_categories(db)


@router.get("", response_model=List[ProductListItem])
def search_products(
    q: Optional[str] = Query(default=None, description="Free-text search on product name"),
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    products = product_service.search_products(
        db, query=q, category=category, color=color, size=size,
        min_price=min_price, max_price=max_price, limit=limit,
    )
    return [product_service.to_list_item(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return product_service.get_product(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
