"""Configuration management for the extraction service."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Database configuration
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="esg_intelligence", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    
    # Google AI configuration
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    
    # RabbitMQ configuration
    rabbitmq_host: str = Field(default="rabbitmq", alias="RABBITMQ_HOST")
    rabbitmq_user: str = Field(default="guest", alias="RABBITMQ_DEFAULT_USER")
    rabbitmq_password: str = Field(default="guest", alias="RABBITMQ_DEFAULT_PASS")
    extraction_queue: str = Field(default="extraction-tasks", alias="EXTRACTION_QUEUE_NAME")
    
    # Service configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    initial_retry_delay: float = Field(default=1.0, alias="INITIAL_RETRY_DELAY")
    
    # Monitoring configuration
    health_port: int = Field(default=8080, alias="HEALTH_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Global config instance
config = Config()
