"""Database package for API Gateway."""

from .models import (
    Base,
    CompanyCatalog,
    IngestionMetadata,
    DocumentEmbedding,
    BRSRIndicator,
    ExtractedIndicator,
    ESGScore,
)
from .connection import (
    get_db,
    get_db_context,
    engine,
    SessionLocal,
    check_database_connection,
    close_database_connections,
    handle_database_error,
    DatabaseConnectionError,
    DatabaseQueryError,
)

__all__ = [
    "Base",
    "CompanyCatalog",
    "IngestionMetadata",
    "DocumentEmbedding",
    "BRSRIndicator",
    "ExtractedIndicator",
    "ESGScore",
    "get_db",
    "get_db_context",
    "engine",
    "SessionLocal",
    "check_database_connection",
    "close_database_connections",
    "handle_database_error",
    "DatabaseConnectionError",
    "DatabaseQueryError",
]
