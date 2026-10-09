from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DashboardStats(BaseModel):
    total_products: int
    total_orders: int
    pending_orders: int
    completed_orders: int
    demo_sales_amount: float
    low_stock_products: int
