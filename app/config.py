from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./kosar.db"
    base_url: str = "http://localhost:8000"
    admin_username: str = "admin"
    admin_password: str = "change-this-before-production"
    app_secret: str = "development-only-secret"
    encryption_key: str = ""
    bale_bot_token: str = ""
    bale_webhook_secret: str = ""
    photo_retention_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
