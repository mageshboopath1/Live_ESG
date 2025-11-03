"""
Pytest configuration and shared fixtures for integration tests
"""
import pytest
import psycopg2
import os
from typing import Generator


@pytest.fixture(scope="session")
def db_connection() -> Generator:
    """
    Provide a database connection for tests.
    This connection is shared across all tests in a session.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "moz"),
        user=os.getenv("DB_USER", "drfitz"),
        password=os.getenv("DB_PASSWORD", "h4i1hydr4")
    )
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """
    Provide a database cursor for tests.
    Automatically rolls back changes after each test.
    """
    cursor = db_connection.cursor()
    yield cursor
    db_connection.rollback()
    cursor.close()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for API Gateway"""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def frontend_base_url() -> str:
    """Base URL for Frontend"""
    return os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def minio_config() -> dict:
    """MinIO configuration"""
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "esg_minio"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "esg_secret"),
        "secure": os.getenv("MINIO_SECURE", "false").lower() == "true"
    }


@pytest.fixture(scope="session")
def rabbitmq_config() -> dict:
    """RabbitMQ configuration"""
    return {
        "host": os.getenv("RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("RABBITMQ_PORT", "5672")),
        "user": os.getenv("RABBITMQ_USER", "esg_rabbitmq"),
        "password": os.getenv("RABBITMQ_PASSWORD", "esg_secret")
    }


@pytest.fixture(scope="session")
def redis_config() -> dict:
    """Redis configuration"""
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0"))
    }


@pytest.fixture(scope="session")
def api_key() -> str:
    """
    Provide API key for authenticated requests.
    Reads from environment variable or .test_api_key file.
    """
    # Try environment variable first
    key = os.getenv("TEST_API_KEY")
    
    if not key:
        # Try reading from .test_api_key file
        key_file = os.path.join(os.path.dirname(__file__), ".test_api_key")
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                key = f.read().strip()
    
    if not key:
        pytest.skip("No API key available. Run tests/utils/generate_test_api_key.py first.")
    
    return key


@pytest.fixture(scope="session")
def auth_headers(api_key) -> dict:
    """Provide authentication headers for API requests"""
    return {"X-API-Key": api_key}
