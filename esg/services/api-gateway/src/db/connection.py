"""Database connection management with pooling and error handling."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=10,  # Number of connections to maintain in the pool
    max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    pool_pre_ping=True,  # Enable connection health checks before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Connection pool event listeners for monitoring and debugging
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new database connection is created."""
    logger.debug("Database connection established")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    logger.debug("Connection returned to pool")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Provides a database session with automatic cleanup and error handling.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/companies")
        def get_companies(db: Session = Depends(get_db)):
            return db.query(CompanyCatalog).all()
    """
    db = SessionLocal()
    try:
        yield db
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database operation: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI.
    
    Provides a database session with automatic cleanup and error handling
    for use in scripts, background tasks, or other non-FastAPI contexts.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_context() as db:
            companies = db.query(CompanyCatalog).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database operation: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is successful, False otherwise
        
    Example:
        if check_database_connection():
            print("Database is accessible")
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection check successful")
        return True
    except exc.SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during connection check: {str(e)}")
        return False


def close_database_connections():
    """
    Close all database connections and dispose of the engine.
    
    Should be called during application shutdown to ensure clean cleanup.
    
    Example:
        @app.on_event("shutdown")
        def shutdown_event():
            close_database_connections()
    """
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


# Custom exception classes for better error handling
class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""

    pass


class DatabaseQueryError(Exception):
    """Raised when a database query fails."""

    pass


def handle_database_error(error: Exception) -> dict:
    """
    Handle database errors and return appropriate error response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        dict: Error response with status code and message
    """
    if isinstance(error, exc.IntegrityError):
        logger.error(f"Database integrity error: {str(error)}")
        return {
            "status_code": 409,
            "detail": "Data integrity constraint violated. The operation conflicts with existing data.",
        }
    elif isinstance(error, exc.OperationalError):
        logger.error(f"Database operational error: {str(error)}")
        return {
            "status_code": 503,
            "detail": "Database service is temporarily unavailable. Please try again later.",
        }
    elif isinstance(error, exc.DataError):
        logger.error(f"Database data error: {str(error)}")
        return {
            "status_code": 400,
            "detail": "Invalid data format or type provided.",
        }
    elif isinstance(error, exc.SQLAlchemyError):
        logger.error(f"Database error: {str(error)}")
        return {
            "status_code": 500,
            "detail": "An unexpected database error occurred.",
        }
    else:
        logger.error(f"Unexpected error: {str(error)}")
        return {
            "status_code": 500,
            "detail": "An unexpected error occurred.",
        }
