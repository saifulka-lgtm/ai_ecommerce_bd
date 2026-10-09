import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_admin
from app.services import auth_service, product_service, order_service
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, DashboardStats, AdminChatRequest
from app.ai import admin_assistant
from app.schemas.product import ProductOut, ProductCreate, ProductUpdate, VariantCreate, VariantUpdate, VariantOut, CategoryOut, CategoryCreate
from app.schemas.order import OrderOut, UpdateOrderStatusRequest
from app.models.ai_conversation import AIToolLog

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- Auth ----

@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest):
    try:
        token = auth_service.authenticate_admin(payload.username, payload.password)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return AdminLoginResponse(access_token=token)


# ---- Dashboard ----

@router.get("/dashboard", response_model=DashboardStats, dependencies=[Depends(require_admin)])
def dashboard(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.order_status == OrderStatus.pending).count()
    completed_orders = db.query(Order).filter(Order.order_status == OrderStatus.delivered).count()
    demo_sales_amount = sum(float(o.total) for o in db.query(Order).filter(Order.payment_status == "DEMO_SUCCESS").all())
    low_stock = len(product_service.low_stock_products(db))

    return DashboardStats(
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        demo_sales_amount=round(demo_sales_amount, 2),
        low_stock_products=low_stock,
    )


# ---- Category management ----

@router.post("/categories", response_model=CategoryOut, dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    return product_service.get_or_create_category(db, payload.name)


# ---- Product management ----

@router.get("/products", response_model=List[ProductOut], dependencies=[Depends(require_admin)])
def list_products(db: Session = Depends(get_db)):
    return product_service.search_products(db, active_only=False, limit=1000)


@router.post("/products", response_model=ProductOut, dependencies=[Depends(require_admin)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return product_service.create_product(db, payload)


@router.put("/products/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db)):
    try:
        return product_service.update_product(db, product_id, payload)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        product_service.delete_product(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}


@router.post("/products/{product_id}/variants", response_model=VariantOut, dependencies=[Depends(require_admin)])
def add_variant(product_id: uuid.UUID, payload: VariantCreate, db: Session = Depends(get_db)):
    try:
        return product_service.add_variant(db, product_id, payload)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.put("/variants/{variant_id}", response_model=VariantOut, dependencies=[Depends(require_admin)])
def update_variant(variant_id: uuid.UUID, payload: VariantUpdate, db: Session = Depends(get_db)):
    try:
        return product_service.update_variant(db, variant_id, payload)
    except product_service.VariantNotFoundError:
        raise HTTPException(status_code=404, detail="Variant not found")


# ---- Order management ----

@router.get("/orders", response_model=List[OrderOut], dependencies=[Depends(require_admin)])
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    orders = order_service.list_all_orders(db, status=status)
    return [order_service.to_out_dict(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut, dependencies=[Depends(require_admin)])
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        order = order_service.get_order_by_id(db, order_id)
    except order_service.OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_service.to_out_dict(order)


@router.put("/orders/{order_id}/status", response_model=OrderOut, dependencies=[Depends(require_admin)])
def update_order_status(order_id: uuid.UUID, payload: UpdateOrderStatusRequest, db: Session = Depends(get_db)):
    try:
        order = order_service.update_order_status(db, order_id, payload.order_status, payload.payment_status)
    except order_service.OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_service.to_out_dict(order)


# ---- Admin AI assistant (order status by chat) ----

@router.post("/ai-chat", dependencies=[Depends(require_admin)])
def admin_ai_chat(payload: AdminChatRequest, db: Session = Depends(get_db)):
    return admin_assistant.handle_admin_message(db, payload.message)


# ---- AI activity log ----

@router.get("/ai-logs", dependencies=[Depends(require_admin)])
def list_ai_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = (
        db.query(AIToolLog)
        .order_by(AIToolLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(log.id),
            "conversation_id": str(log.conversation_id),
            "customer_message": log.customer_message,
            "tool_name": log.tool_name,
            "tool_arguments": log.tool_arguments,
            "tool_result": log.tool_result,
            "execution_time_ms": log.execution_time_ms,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
