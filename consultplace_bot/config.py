# consultplace_bot/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Глобальные переменные окружения для Telegram-бота."""

    # === Telegram ===
    telegram_token: str

    # === CRM-backend ===
    backend_base_url: str       # например: https://crm.consultplace.pro
    backend_user: str           # service-account login
    backend_password: str       # service-account password

    # === Redis ===
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",        # из какого файла читать по-умолчанию
        extra="ignore",         # игнорировать лишние переменные
    )
    database_url: str = "postgresql+asyncpg://user:pass@localhost/dbname"


# единый инстанс, импортируем где нужно
settings = Settings()