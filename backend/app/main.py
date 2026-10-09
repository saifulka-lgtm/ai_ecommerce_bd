from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import products, cart, orders, admin, chat

settings = get_settings()

app = FastAPI(
    title="AI-Operated E-Commerce Demo API",
    description=(
        "Backend for a demo clothing store where an AI agent, using controlled "
        "backend tools, is the primary operator of the customer shopping workflow. "
        "This is a TESTING/DEMO project — no real payments are processed."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_provider": settings.ai_provider, "environment": settings.environment}
