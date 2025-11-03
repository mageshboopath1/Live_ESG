"""JWT token generation and validation."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from ..config import settings

# Security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model."""

    user_id: Optional[int] = None
    username: Optional[str] = None
    api_key_id: Optional[int] = None
    scopes: list[str] = []


class User(BaseModel):
    """User model for authentication."""

    id: int
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token payload data
        expires_delta: Optional expiration time delta
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token = create_access_token({"sub": "user123", "user_id": 1})
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        api_key_id: int = payload.get("api_key_id")
        scopes: list = payload.get("scopes", [])
        
        if username is None and api_key_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            username=username,
            user_id=user_id,
            api_key_id=api_key_id,
            scopes=scopes
        )
        
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        TokenData: Current user token data
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    token_data = verify_token(token)
    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Get current active user.
    
    Args:
        current_user: Current user token data
        
    Returns:
        TokenData: Active user token data
        
    Raises:
        HTTPException: If user is inactive
    """
    # In a real implementation, you would check the database
    # to verify the user is still active
    return current_user


def create_api_key_token(api_key_id: int, scopes: list[str]) -> str:
    """
    Create a JWT token for API key authentication.
    
    Args:
        api_key_id: API key ID
        scopes: List of permission scopes
        
    Returns:
        str: Encoded JWT token
    """
    data = {
        "api_key_id": api_key_id,
        "scopes": scopes,
        "type": "api_key"
    }
    
    # API keys don't expire by default, but we set a long expiration
    expires_delta = timedelta(days=365)
    
    return create_access_token(data, expires_delta)


def verify_api_key_token(token: str) -> TokenData:
    """
    Verify an API key token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or not an API key token
    """
    token_data = verify_token(token)
    
    if token_data.api_key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data
