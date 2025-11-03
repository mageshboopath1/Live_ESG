#!/usr/bin/env python3
"""
Pipeline Configuration Module

Centralized configuration for the ESG pipeline end-to-end testing system.
All configuration values can be overridden via environment variables.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "moz"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "drfitz"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "h4i1hydr4"))
    
    @property
    def connection_dict(self) -> dict:
        """Return connection parameters as dictionary for psycopg2."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.name,
            "user": self.user,
            "password": self.password
        }
    
    @property
    def connection_string(self) -> str:
        """Return PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class MinIOConfig:
    """MinIO object storage configuration."""
    
    endpoint: str = field(default_factory=lambda: os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
    access_key: str = field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", os.getenv("MINIO_ROOT_USER", "esg_minio")))
    secret_key: str = field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", os.getenv("MINIO_ROOT_PASSWORD", "esg_secret")))
    bucket: str = field(default_factory=lambda: os.getenv("BUCKET_NAME", "esg-reports"))
    secure: bool = field(default_factory=lambda: os.getenv("MINIO_SECURE", "false").lower() == "true")


@dataclass
class RabbitMQConfig:
    """RabbitMQ message queue configuration."""
    
    host: str = field(default_factory=lambda: os.getenv("RABBITMQ_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_PORT", "5672")))
    user: str = field(default_factory=lambda: os.getenv("RABBITMQ_DEFAULT_USER", "esg_rabbitmq"))
    password: str = field(default_factory=lambda: os.getenv("RABBITMQ_DEFAULT_PASS", "esg_secret"))
    embedding_queue: str = field(default_factory=lambda: os.getenv("QUEUE_NAME", "embedding-tasks"))
    extraction_queue: str = field(default_factory=lambda: os.getenv("EXTRACTION_QUEUE_NAME", "extraction-tasks"))
    
    # Connection settings
    heartbeat: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_HEARTBEAT", "600")))
    blocked_connection_timeout: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_BLOCKED_TIMEOUT", "300")))


@dataclass
class EmbeddingConfig:
    """Embedding service configuration."""
    
    # Model configuration
    model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"))
    dimensions: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSIONS", "3072")))
    
    # Processing configuration
    batch_size: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_BATCH_SIZE", "32")))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1500")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))
    max_chunks_per_document: int = field(default_factory=lambda: int(os.getenv("MAX_CHUNKS_PER_DOCUMENT", "1000")))
    
    # Retry configuration
    max_retries: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_MAX_RETRIES", "3")))
    initial_retry_delay: float = field(default_factory=lambda: float(os.getenv("EMBEDDING_RETRY_DELAY", "1.0")))
    retry_backoff_multiplier: float = field(default_factory=lambda: float(os.getenv("EMBEDDING_RETRY_BACKOFF", "2.0")))


@dataclass
class ExtractionConfig:
    """Extraction service configuration."""
    
    # Model configuration
    model: str = field(default_factory=lambda: os.getenv("EXTRACTION_MODEL", "gemini-2.0-flash-exp"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EXTRACTION_EMBEDDING_MODEL", "gemini-embedding-001"))
    embedding_dimensions: int = field(default_factory=lambda: int(os.getenv("EXTRACTION_EMBEDDING_DIMENSIONS", "3072")))
    
    # Processing configuration
    batch_size: int = field(default_factory=lambda: int(os.getenv("EXTRACTION_BATCH_SIZE", "10")))
    check_embeddings_before_extraction: bool = field(
        default_factory=lambda: os.getenv("CHECK_EMBEDDINGS_BEFORE_EXTRACTION", "true").lower() == "true"
    )
    
    # Retry configuration
    max_retries: int = field(default_factory=lambda: int(os.getenv("EXTRACTION_MAX_RETRIES", "3")))
    initial_retry_delay: float = field(default_factory=lambda: float(os.getenv("EXTRACTION_RETRY_DELAY", "1.0")))
    retry_backoff_multiplier: float = field(default_factory=lambda: float(os.getenv("EXTRACTION_RETRY_BACKOFF", "2.0")))
    
    # Embedding check configuration
    embedding_check_max_attempts: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_CHECK_MAX_ATTEMPTS", "10")))
    embedding_check_delay: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_CHECK_DELAY", "30")))


@dataclass
class QueueMonitoringConfig:
    """Queue monitoring configuration for pipeline orchestration."""
    
    # Timeout settings (in seconds)
    embedding_timeout: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_TIMEOUT", "3600")))  # 1 hour
    extraction_timeout: int = field(default_factory=lambda: int(os.getenv("EXTRACTION_TIMEOUT", "7200")))  # 2 hours
    
    # Monitoring intervals (in seconds)
    check_interval: int = field(default_factory=lambda: int(os.getenv("QUEUE_CHECK_INTERVAL", "10")))  # Check every 10 seconds
    empty_queue_wait: int = field(default_factory=lambda: int(os.getenv("EMPTY_QUEUE_WAIT", "30")))  # Wait 30s to confirm empty
    
    # Progress reporting
    progress_log_interval: int = field(default_factory=lambda: int(os.getenv("PROGRESS_LOG_INTERVAL", "60")))  # Log every 60s


@dataclass
class IngestionConfig:
    """Ingestion service configuration."""
    
    # Delay for extraction tasks (in seconds)
    extraction_task_delay: int = field(default_factory=lambda: int(os.getenv("EXTRACTION_TASK_DELAY", "300")))  # 5 minutes
    
    # Retry configuration
    max_retries: int = field(default_factory=lambda: int(os.getenv("INGESTION_MAX_RETRIES", "3")))
    initial_retry_delay: float = field(default_factory=lambda: float(os.getenv("INGESTION_RETRY_DELAY", "1.0")))
    
    # Processing limits
    max_concurrent_downloads: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5")))


@dataclass
class GoogleAIConfig:
    """Google Generative AI configuration."""
    
    api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", os.getenv("GENAI_API_KEY", "")))
    
    # Rate limiting
    requests_per_minute: int = field(default_factory=lambda: int(os.getenv("GOOGLE_API_RPM", "60")))
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("GOOGLE_API_MAX_CONCURRENT", "5")))


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    minio: MinIOConfig = field(default_factory=MinIOConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    queue_monitoring: QueueMonitoringConfig = field(default_factory=QueueMonitoringConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    google_ai: GoogleAIConfig = field(default_factory=GoogleAIConfig)
    
    # General settings
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            list: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required API key
        if not self.google_ai.api_key:
            errors.append("GOOGLE_API_KEY is required but not set")
        
        # Validate embedding dimensions
        if self.embedding.dimensions not in [768, 3072]:
            errors.append(f"EMBEDDING_DIMENSIONS must be 768 or 3072, got {self.embedding.dimensions}")
        
        # Validate extraction embedding dimensions match
        if self.extraction.embedding_dimensions != self.embedding.dimensions:
            errors.append(
                f"EXTRACTION_EMBEDDING_DIMENSIONS ({self.extraction.embedding_dimensions}) "
                f"must match EMBEDDING_DIMENSIONS ({self.embedding.dimensions})"
            )
        
        # Validate timeouts
        if self.queue_monitoring.embedding_timeout < 60:
            errors.append("EMBEDDING_TIMEOUT must be at least 60 seconds")
        
        if self.queue_monitoring.extraction_timeout < 60:
            errors.append("EXTRACTION_TIMEOUT must be at least 60 seconds")
        
        # Validate check intervals
        if self.queue_monitoring.check_interval < 1:
            errors.append("QUEUE_CHECK_INTERVAL must be at least 1 second")
        
        if self.queue_monitoring.empty_queue_wait < 1:
            errors.append("EMPTY_QUEUE_WAIT must be at least 1 second")
        
        # Validate retry settings
        if self.embedding.max_retries < 0:
            errors.append("EMBEDDING_MAX_RETRIES must be non-negative")
        
        if self.extraction.max_retries < 0:
            errors.append("EXTRACTION_MAX_RETRIES must be non-negative")
        
        # Validate batch sizes
        if self.embedding.batch_size < 1:
            errors.append("EMBEDDING_BATCH_SIZE must be at least 1")
        
        if self.extraction.batch_size < 1:
            errors.append("EXTRACTION_BATCH_SIZE must be at least 1")
        
        return errors
    
    def print_summary(self):
        """Print configuration summary."""
        print("=" * 70)
        print("Pipeline Configuration Summary")
        print("=" * 70)
        
        print("\n📊 Database:")
        print(f"  Host: {self.database.host}:{self.database.port}")
        print(f"  Database: {self.database.name}")
        print(f"  User: {self.database.user}")
        
        print("\n📦 MinIO:")
        print(f"  Endpoint: {self.minio.endpoint}")
        print(f"  Bucket: {self.minio.bucket}")
        print(f"  Secure: {self.minio.secure}")
        
        print("\n📨 RabbitMQ:")
        print(f"  Host: {self.rabbitmq.host}:{self.rabbitmq.port}")
        print(f"  Embedding Queue: {self.rabbitmq.embedding_queue}")
        print(f"  Extraction Queue: {self.rabbitmq.extraction_queue}")
        
        print("\n🔢 Embedding:")
        print(f"  Model: {self.embedding.model}")
        print(f"  Dimensions: {self.embedding.dimensions}")
        print(f"  Batch Size: {self.embedding.batch_size}")
        print(f"  Max Retries: {self.embedding.max_retries}")
        
        print("\n🔍 Extraction:")
        print(f"  Model: {self.extraction.model}")
        print(f"  Embedding Model: {self.extraction.embedding_model}")
        print(f"  Embedding Dimensions: {self.extraction.embedding_dimensions}")
        print(f"  Batch Size: {self.extraction.batch_size}")
        print(f"  Check Embeddings: {self.extraction.check_embeddings_before_extraction}")
        print(f"  Max Retries: {self.extraction.max_retries}")
        
        print("\n⏱️  Queue Monitoring:")
        print(f"  Embedding Timeout: {self.queue_monitoring.embedding_timeout}s")
        print(f"  Extraction Timeout: {self.queue_monitoring.extraction_timeout}s")
        print(f"  Check Interval: {self.queue_monitoring.check_interval}s")
        print(f"  Empty Queue Wait: {self.queue_monitoring.empty_queue_wait}s")
        
        print("\n📥 Ingestion:")
        print(f"  Extraction Task Delay: {self.ingestion.extraction_task_delay}s")
        print(f"  Max Retries: {self.ingestion.max_retries}")
        
        print("\n🔑 Google AI:")
        api_key_display = f"{self.google_ai.api_key[:10]}..." if self.google_ai.api_key else "(not set)"
        print(f"  API Key: {api_key_display}")
        print(f"  Requests Per Minute: {self.google_ai.requests_per_minute}")
        
        print("\n⚙️  General:")
        print(f"  Log Level: {self.log_level}")
        print(f"  Debug: {self.debug}")
        
        print("=" * 70)


# Global configuration instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """
    Get or create global configuration instance.
    
    Returns:
        PipelineConfig: Global configuration instance
    """
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config


def reload_config() -> PipelineConfig:
    """
    Reload configuration from environment variables.
    
    Returns:
        PipelineConfig: New configuration instance
    """
    global _config
    _config = PipelineConfig()
    return _config


# Convenience functions for backward compatibility
def get_db_config() -> dict:
    """Get database configuration as dictionary."""
    return get_config().database.connection_dict


def get_minio_config() -> dict:
    """Get MinIO configuration as dictionary."""
    config = get_config().minio
    return {
        "endpoint": config.endpoint,
        "access_key": config.access_key,
        "secret_key": config.secret_key,
        "bucket": config.bucket,
        "secure": config.secure
    }


def get_rabbitmq_config() -> dict:
    """Get RabbitMQ configuration as dictionary."""
    config = get_config().rabbitmq
    return {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "password": config.password,
        "embedding_queue": config.embedding_queue,
        "extraction_queue": config.extraction_queue
    }


def get_pipeline_config() -> dict:
    """Get pipeline monitoring configuration as dictionary."""
    config = get_config().queue_monitoring
    return {
        "embedding_timeout": config.embedding_timeout,
        "extraction_timeout": config.extraction_timeout,
        "queue_check_interval": config.check_interval,
        "empty_queue_wait": config.empty_queue_wait
    }


if __name__ == "__main__":
    """Print configuration when run as script."""
    config = get_config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("❌ Configuration Validation Errors:")
        for error in errors:
            print(f"  • {error}")
        print()
    
    # Print summary
    config.print_summary()
