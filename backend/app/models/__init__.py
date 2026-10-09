"""
Import every model here so that Base.metadata is fully populated
when Alembic or create_all() runs.
"""
from app.models.user import User, UserRole  # noqa
from app.models.category import Category  # noqa
from app.models.product import Product, ProductVariant  # noqa
from app.models.cart import Cart, CartItem  # noqa
from app.models.order import Order, OrderItem, OrderStatus  # noqa
from app.models.payment import Payment  # noqa
from app.models.ai_conversation import AIConversation, AIMessage, AIToolLog  # noqa
