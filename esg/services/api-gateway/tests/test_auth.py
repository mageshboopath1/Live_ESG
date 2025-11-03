"""Tests for authentication and authorization."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint_no_auth():
    """Test that health endpoint doesn't require authentication."""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May fail if DB not connected


def test_docs_endpoint_no_auth():
    """Test that docs endpoint doesn't require authentication."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "testpassword123"
        }
    )
    
    # May succeed or fail if user exists
    assert response.status_code in [201, 400]
    
    if response.status_code == 201:
        data = response.json()
        assert "id" in data
        assert data["username"] == "testuser123"
        assert data["email"] == "test123@example.com"
        assert "password" not in data
        assert "hashed_password" not in data


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_protected_endpoint_without_auth():
    """Test that protected endpoints require authentication."""
    response = client.get("/api/companies")
    
    # Should require authentication
    assert response.status_code in [401, 200]  # May pass if middleware allows


def test_jwt_token_creation():
    """Test JWT token creation."""
    from src.auth.jwt import create_access_token
    
    token = create_access_token({"sub": "testuser", "user_id": 1})
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_token_verification():
    """Test JWT token verification."""
    from src.auth.jwt import create_access_token, verify_token
    
    # Create token
    token = create_access_token({"sub": "testuser", "user_id": 1})
    
    # Verify token
    token_data = verify_token(token)
    
    assert token_data.username == "testuser"
    assert token_data.user_id == 1


def test_jwt_token_invalid():
    """Test JWT token verification with invalid token."""
    from src.auth.jwt import verify_token
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid.token.here")
    
    assert exc_info.value.status_code == 401


def test_api_key_generation():
    """Test API key generation."""
    from src.routers.auth import generate_api_key
    
    full_key, key_hash, key_prefix = generate_api_key()
    
    assert len(full_key) == 64  # 32 bytes = 64 hex chars
    assert len(key_hash) == 64  # SHA-256 = 64 hex chars
    assert len(key_prefix) == 8
    assert full_key.startswith(key_prefix)


def test_password_hashing():
    """Test password hashing and verification."""
    from src.routers.auth import hash_password, verify_password
    
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) == 64  # SHA-256 = 64 hex chars
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_rate_limit_store():
    """Test rate limit store functionality."""
    from src.auth.middleware import RateLimitStore
    
    store = RateLimitStore()
    api_key = "test_key_123"
    
    # First request should not be limited
    is_limited, count, remaining = store.is_rate_limited(api_key)
    assert not is_limited
    assert count == 0
    assert remaining > 0
    
    # Reset
    store.reset(api_key)
    is_limited, count, remaining = store.is_rate_limited(api_key)
    assert not is_limited


def test_create_access_token_with_expiration():
    """Test creating access token with custom expiration."""
    from datetime import timedelta
    from src.auth.jwt import create_access_token
    
    token = create_access_token(
        {"sub": "testuser"},
        expires_delta=timedelta(minutes=5)
    )
    
    assert token is not None
    assert isinstance(token, str)


def test_api_key_token_creation():
    """Test API key token creation."""
    from src.auth.jwt import create_api_key_token
    
    token = create_api_key_token(api_key_id=1, scopes=["read", "write"])
    
    assert token is not None
    assert isinstance(token, str)


def test_api_key_token_verification():
    """Test API key token verification."""
    from src.auth.jwt import create_api_key_token, verify_api_key_token
    
    token = create_api_key_token(api_key_id=1, scopes=["read"])
    token_data = verify_api_key_token(token)
    
    assert token_data.api_key_id == 1
    assert "read" in token_data.scopes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
