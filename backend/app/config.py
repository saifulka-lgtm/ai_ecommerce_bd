"""
Application configuration.

All settings come from environment variables (see .env.example).
Never hard-code secrets or credentials here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_ecommerce_bd"

    # AI provider: mock | claude | ollama
    ai_provider: str = "mock"
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Security
    secret_key: str = "dev-secret-key-change-me"
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # AI fulfillment agent: moves orders PENDING -> CONFIRMED -> SHIPPED -> DELIVERED
    # on its own. Times are demo-friendly seconds an order waits in each status.
    auto_fulfillment_enabled: bool = True
    fulfillment_poll_seconds: int = 10
    fulfillment_confirm_after_seconds: int = 30
    fulfillment_ship_after_seconds: int = 90
    fulfillment_deliver_after_seconds: int = 180

    # Demo business rules
    demo_delivery_charge: float = 60.0
    free_delivery_threshold: float = 2000.0

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
