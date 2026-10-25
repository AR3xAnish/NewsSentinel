import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "YGF AI News Intelligence Agent"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./news_intelligence.db"

    # Ollama Local LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_TIMEOUT_SECONDS: int = 90
    OLLAMA_TEMPERATURE: float = 0.2

    # Ingestion & Collection
    COLLECTION_LOOKBACK_HOURS: int = 48
    MAX_ARTICLES_PER_FEED: int = 10
    HTTP_TIMEOUT_SECONDS: int = 15
    USER_AGENT: str = "YGFNewsIntelligence/1.0 (+https://ygf-ngo.org; evaluation bot)"

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_MINUTES: int = 60

    # Telegram Delivery
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    DAILY_DIGEST_ENABLED: bool = True
    DAILY_DIGEST_TIME: str = "09:00"  # 24-hour HH:MM format for daily scheduled delivery
    DAILY_DIGEST_MAX_STORIES: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
