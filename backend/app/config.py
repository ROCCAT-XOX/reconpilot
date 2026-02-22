import logging

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ReconForge"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # Only this has a default
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database — REQUIRED, no default. App fails at startup if missing.
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security — REQUIRED, no default. App fails at startup if missing.
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # Tool API Keys
    WPSCAN_API_TOKEN: str = ""
    SHODAN_API_KEY: str = ""
    CENSYS_API_ID: str = ""
    CENSYS_API_SECRET: str = ""
    VIRUSTOTAL_API_KEY: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",")]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
