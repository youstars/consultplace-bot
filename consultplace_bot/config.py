# consultplace_bot/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_token:   str
    backend_base_url: str
    backend_user:     str
    backend_password: str

    database_url: str = "sqlite+aiosqlite:///./test.db"
    redis_url:    str = "redis://localhost:6379/0"


# ----------------------------------------------------------------------
settings = Settings()            #  ← вернуть эту строку