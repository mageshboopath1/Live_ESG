"""Authentication dependencies for route protection."""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from .jwt import get_current_user, TokenData


def require_auth(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to require authentication for a route.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        TokenData: Authenticated user data
        
    Raises:
        HTTPException: If user is not authenticated
        
    Example:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(require_auth)):
            return {"user_id": user.user_id}
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_api_key(request: Request) -> str:
    """
    Dependency to require API key for a route.
    
    Args:
        request: FastAPI request
        
    Returns:
        str: API key from request
        
    Raises:
        HTTPException: If API key is not provided or invalid
        
    Example:
        @app.get("/api-protected")
        async def api_protected_route(api_key: str = Depends(require_api_key)):
            return {"api_key": api_key[:10] + "..."}
    """
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # In production, validate API key against database
    if len(api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key


def require_scopes(required_scopes: List[str]):
    """
    Dependency factory to require specific scopes.
    
    Args:
        required_scopes: List of required permission scopes
        
    Returns:
        Dependency function that checks scopes
        
    Example:
        @app.get("/admin")
        async def admin_route(user: TokenData = Depends(require_scopes(["admin"]))):
            return {"message": "Admin access granted"}
    """
    def check_scopes(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """Check if user has required scopes."""
        user_scopes = set(current_user.scopes)
        required = set(required_scopes)
        
        if not required.issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scopes: {required_scopes}",
            )
        
        return current_user
    
    return check_scopes


def optional_auth(
    request: Request
) -> Optional[TokenData]:
    """
    Dependency for optional authentication.
    
    Returns user data if authenticated, None otherwise.
    Useful for endpoints that have different behavior for authenticated users.
    
    Args:
        request: FastAPI request
        
    Returns:
        Optional[TokenData]: User data if authenticated, None otherwise
        
    Example:
        @app.get("/public")
        async def public_route(user: Optional[TokenData] = Depends(optional_auth)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello guest"}
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        from .jwt import verify_token
        token = auth_header.split(" ")[1]
        return verify_token(token)
    except Exception:
        return None
