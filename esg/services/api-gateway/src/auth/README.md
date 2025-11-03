# Authentication and Authorization

This module provides JWT-based authentication and API key management for the ESG Intelligence Platform API Gateway.

## Features

- **JWT Authentication**: Token-based authentication with configurable expiration
- **API Key Management**: Create, list, and revoke API keys for programmatic access
- **Rate Limiting**: Per-API-key rate limiting (100 requests per minute by default)
- **User Management**: User registration, login, and profile management
- **Protected Routes**: Easy-to-use decorators for route protection
- **Scope-based Authorization**: Fine-grained permission control with scopes

## Components

### 1. JWT Token Management (`jwt.py`)

Handles JWT token creation, validation, and user authentication.

**Key Functions:**
- `create_access_token(data, expires_delta)`: Create a JWT access token
- `verify_token(token)`: Verify and decode a JWT token
- `get_current_user(credentials)`: Get current user from JWT token
- `create_api_key_token(api_key_id, scopes)`: Create a long-lived API key token

**Example:**
```python
from src.auth.jwt import create_access_token

token = create_access_token(
    data={"sub": "username", "user_id": 1, "scopes": ["read", "write"]},
    expires_delta=timedelta(minutes=30)
)
```

### 2. Middleware (`middleware.py`)

Provides authentication and rate limiting middleware.

**Components:**
- `APIKeyMiddleware`: Validates API keys from `X-API-Key` header
- `RateLimitMiddleware`: Enforces rate limits per API key
- `RateLimitStore`: In-memory rate limit tracking

**Configuration:**
- Rate limit: 100 requests per 60-second window (configurable in `config.py`)
- Excluded paths: `/`, `/health`, `/docs`, `/redoc`, `/openapi.json`, `/api/auth/*`

### 3. Dependencies (`dependencies.py`)

FastAPI dependencies for route protection.

**Available Dependencies:**
- `require_auth()`: Require JWT authentication
- `require_api_key()`: Require API key in header
- `require_scopes(scopes)`: Require specific permission scopes
- `optional_auth()`: Optional authentication (returns None if not authenticated)

**Example:**
```python
from fastapi import APIRouter, Depends
from src.auth.dependencies import require_auth, require_scopes

router = APIRouter()

@router.get("/protected")
async def protected_route(user = Depends(require_auth)):
    return {"user_id": user.user_id}

@router.get("/admin")
async def admin_route(user = Depends(require_scopes(["admin"]))):
    return {"message": "Admin access granted"}
```

### 4. Authentication Router (`routers/auth.py`)

API endpoints for user and API key management.

**Endpoints:**

#### User Management
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login with username/password
- `GET /api/auth/me`: Get current user information

#### API Key Management
- `POST /api/auth/api-keys`: Create a new API key
- `GET /api/auth/api-keys`: List all API keys for current user
- `GET /api/auth/api-keys/{key_id}`: Get specific API key details
- `DELETE /api/auth/api-keys/{key_id}`: Revoke an API key

## Usage

### 1. User Registration and Login

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'

# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=securepassword123"

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Using JWT Token

```bash
# Access protected endpoint with JWT token
curl -X GET http://localhost:8000/api/companies \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Creating and Using API Keys

```bash
# Create an API key (requires JWT authentication)
curl -X POST http://localhost:8000/api/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "Production API Key",
    "scopes": ["read", "write"],
    "expires_in_days": 365
  }'

# Response (API key shown only once):
{
  "id": 1,
  "key_name": "Production API Key",
  "key_prefix": "a1b2c3d4",
  "api_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0",
  "scopes": ["read", "write"],
  "is_active": true,
  "expires_at": "2026-10-28T12:00:00Z",
  "created_at": "2025-10-28T12:00:00Z"
}

# Use API key for authentication
curl -X GET http://localhost:8000/api/companies \
  -H "X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0"
```

### 4. List and Revoke API Keys

```bash
# List all API keys
curl -X GET http://localhost:8000/api/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Revoke an API key
curl -X DELETE http://localhost:8000/api/auth/api-keys/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    scopes JSONB DEFAULT '[]'::jsonb,
    is_active INTEGER DEFAULT 1,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Security Considerations

### Password Hashing
- Passwords are hashed using SHA-256
- In production, consider using bcrypt or argon2 for stronger hashing

### API Key Storage
- API keys are hashed before storage (SHA-256)
- Only the first 8 characters (prefix) are stored in plain text for identification
- Full API key is shown only once during creation

### JWT Configuration
- Secret key should be changed in production (set `SECRET_KEY` in `.env`)
- Default token expiration: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Tokens include user ID, username, and scopes

### Rate Limiting
- Default: 100 requests per 60-second window
- Rate limits are tracked per API key
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` in config

## Testing

Run the authentication tests:

```bash
cd services/api-gateway
uv run pytest test_auth.py -v
```

## Default Test Users

The migration script creates two default users for testing:

1. **Admin User**
   - Username: `admin`
   - Email: `admin@esg-platform.local`
   - Password: `admin123`
   - Role: Admin

2. **Regular User**
   - Username: `testuser`
   - Email: `user@esg-platform.local`
   - Password: `user123`
   - Role: User

**⚠️ Important:** Change or remove these default users in production!

## Configuration

Environment variables in `.env`:

```env
# JWT Settings
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Future Enhancements

- [ ] Implement refresh tokens for long-lived sessions
- [ ] Add OAuth2 support (Google, GitHub, etc.)
- [ ] Implement password reset functionality
- [ ] Add email verification for new users
- [ ] Use Redis for distributed rate limiting
- [ ] Implement more robust password hashing (bcrypt/argon2)
- [ ] Add audit logging for authentication events
- [ ] Implement IP-based rate limiting
- [ ] Add 2FA (Two-Factor Authentication) support
