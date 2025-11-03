"""Configuration management for API Gateway."""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    APP_NAME: str = "ESG Intelligence Platform API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "esg_platform"
    DB_USER: str = "esg_user"
    DB_PASSWORD: str = ""

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-in-production-please-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = 100  # requests per window
    RATE_LIMIT_WINDOW: int = 60  # window size in seconds

    # MinIO settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "esg-reports"
    MINIO_SECURE: bool = False

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_ENABLED: bool = True
    
    # Cache TTL settings (in seconds)
    CACHE_TTL_COMPANY: int = 3600  # 1 hour
    CACHE_TTL_INDICATORS: int = 86400  # 24 hours
    CACHE_TTL_SCORES: int = 3600  # 1 hour

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
