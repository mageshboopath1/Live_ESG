"""Authentication and API key management endpoints."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from ..db.connection import get_db
from ..db.models import User, APIKey
from ..auth.jwt import create_access_token, get_current_user, TokenData
from ..auth.dependencies import require_auth, require_scopes

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response Models
class UserCreate(BaseModel):
    """User creation request model."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyCreate(BaseModel):
    """API key creation request model."""
    key_name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response model."""
    id: int
    key_name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """API key created response with full key (only shown once)."""
    api_key: str


# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (full_key, key_hash, key_prefix)
    """
    # Generate random key (32 bytes = 64 hex chars)
    full_key = secrets.token_hex(32)
    
    # Hash the key for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Store first 8 chars as prefix for identification
    key_prefix = full_key[:8]
    
    return full_key, key_hash, key_prefix


# Authentication endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=1,
        is_admin=0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username and password to get JWT token.
    
    Args:
        form_data: OAuth2 password form data
        db: Database session
        
    Returns:
        TokenResponse: JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "scopes": ["admin"] if user.is_admin else ["user"]
        }
    )
    
    from ..config import settings
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current user from JWT token
        db: Database session
        
    Returns:
        UserResponse: Current user data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# API Key management endpoints
@router.post("/api-keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the authenticated user.
    
    Args:
        key_data: API key creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyCreatedResponse: Created API key (full key only shown once)
    """
    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        user_id=current_user.user_id,
        key_name=key_data.key_name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=key_data.scopes,
        is_active=1,
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Return response with full key (only shown once)
    return APIKeyCreatedResponse(
        id=api_key.id,
        key_name=api_key.key_name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=bool(api_key.is_active),
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        api_key=full_key
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    List all API keys for the authenticated user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[APIKeyResponse]: List of user's API keys
    """
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.user_id).all()
    
    return [
        APIKeyResponse(
            id=key.id,
            key_name=key.key_name,
            key_prefix=key.key_prefix,
            scopes=key.scopes or [],
            is_active=bool(key.is_active),
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            created_at=key.created_at
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Revoke (delete) an API key.
    
    Args:
        key_id: API key ID to revoke
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If API key not found or doesn't belong to user
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.user_id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Mark as inactive instead of deleting
    api_key.is_active = 0
    db.commit()
    
    return None


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyResponse: API key details
        
    Raises:
        HTTPException: If API key not found or doesn't belong to user
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.user_id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse(
        id=api_key.id,
        key_name=api_key.key_name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes or [],
        is_active=bool(api_key.is_active),
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at
    )
