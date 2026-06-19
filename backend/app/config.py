from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "ExamAI Hub API"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-please")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./school_helper.db")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_MODE: str = "sandbox"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/uploads")

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@examaihub.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

    CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS:
            origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
            return origins
        return [self.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def is_production(self) -> bool:
        return not self.DEBUG and self.PAYPAL_MODE != "sandbox"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
