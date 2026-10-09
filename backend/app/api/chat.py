from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.ai.agent import handle_message
from app.config import get_settings
from app.utils.rate_limit import RateLimiter, rate_limited

_limiter = RateLimiter(get_settings().chat_rate_limit_per_minute)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limited(_limiter, "অনেক বেশি মেসেজ পাঠানো হয়েছে, এক মিনিট পর আবার চেষ্টা করুন।")),
):
    result = handle_message(db, payload.session_id, payload.message, payload.customer_name)
    return ChatResponse(**result)
