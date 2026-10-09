import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import products, cart, orders, admin, chat

from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401 - registers every table on Base.metadata
from app.services import fulfillment_service

settings = get_settings()
logger = logging.getLogger("fulfillment")


def _run_fulfillment_once() -> None:
    db = SessionLocal()
    try:
        changes = fulfillment_service.advance_orders(
            db,
            settings.fulfillment_confirm_after_seconds,
            settings.fulfillment_ship_after_seconds,
            settings.fulfillment_deliver_after_seconds,
        )
        for c in changes:
            logger.info("AI fulfillment: %s %s -> %s", c["order_number"], c["from"], c["to"])
    finally:
        db.close()


async def _fulfillment_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_run_fulfillment_once)
        except Exception:  # noqa: BLE001 - the loop must never die
            logger.exception("fulfillment tick failed")
        await asyncio.sleep(settings.fulfillment_poll_seconds)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = None
    if settings.auto_fulfillment_enabled:
        # Only creates tables that are missing (e.g. order_status_events);
        # never alters existing ones.
        Base.metadata.create_all(bind=engine)
        task = asyncio.create_task(_fulfillment_loop())
    yield
    if task:
        task.cancel()

app = FastAPI(
    title="AI-Operated E-Commerce Demo API",
    description=(
        "Backend for a demo clothing store where an AI agent, using controlled "
        "backend tools, is the primary operator of the customer shopping workflow. "
        "This is a TESTING/DEMO project — no real payments are processed."
    ),
    version="1.0.0",
    lifespan=lifespan,
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
