"""
Application configuration.

All settings come from environment variables (see .env.example).
Never hard-code secrets or credentials here.
"""
from functools import lru_cache
from typing import List

from pydantic import model_validator
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
    # Optional: a pbkdf2 hash (python -m app.utils.hash_password) used INSTEAD of
    # the plain admin_password, so no readable password sits in .env.
    admin_password_hash: str = ""

    # Abuse protection (per client IP, in-memory; use Redis for multi-server)
    rate_limit_enabled: bool = True
    chat_rate_limit_per_minute: int = 30
    login_rate_limit_per_minute: int = 5

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

    @model_validator(mode="after")
    def _refuse_insecure_production(self):
        """In production the app refuses to start with demo-grade secrets."""
        if self.environment.lower() == "production":
            problems = []
            if self.secret_key == "dev-secret-key-change-me" or len(self.secret_key) < 32:
                problems.append("SECRET_KEY must be a random string of at least 32 characters")
            if not self.admin_password_hash and self.admin_password in ("admin123", "", "change-me"):
                problems.append("set a strong ADMIN_PASSWORD_HASH (python -m app.utils.hash_password)")
            if problems:
                raise ValueError("Insecure production configuration: " + "; ".join(problems))
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
