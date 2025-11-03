"""Authentication and rate limiting middleware."""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitStore:
    """In-memory rate limit store."""
    
    def __init__(self):
        # Store: {api_key: [(timestamp, count), ...]}
        self._store: Dict[str, list[Tuple[float, int]]] = defaultdict(list)
        self._window_size = 60  # 60 seconds window
        self._max_requests = 100  # 100 requests per minute
    
    def is_rate_limited(self, api_key: str) -> Tuple[bool, int, int]:
        """
        Check if an API key is rate limited.
        
        Args:
            api_key: API key identifier
            
        Returns:
            Tuple of (is_limited, current_count, remaining)
        """
        current_time = time.time()
        window_start = current_time - self._window_size
        
        # Clean old entries
        self._store[api_key] = [
            (ts, count) for ts, count in self._store[api_key]
            if ts > window_start
        ]
        
        # Count requests in current window
        current_count = sum(count for _, count in self._store[api_key])
        
        # Check if rate limited
        is_limited = current_count >= self._max_requests
        remaining = max(0, self._max_requests - current_count)
        
        if not is_limited:
            # Add current request
            self._store[api_key].append((current_time, 1))
        
        return is_limited, current_count, remaining
    
    def reset(self, api_key: str):
        """Reset rate limit for an API key."""
        if api_key in self._store:
            del self._store[api_key]


# Global rate limit store
rate_limit_store = RateLimitStore()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with API key authentication.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or error response
        """
        # Skip authentication for docs and health endpoints
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Skip authentication for auth endpoints
        if request.url.path.startswith("/api/auth"):
            return await call_next(request)
        
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            # Check for Bearer token (JWT)
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API key or Bearer token required"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # If Bearer token exists, let JWT validation handle it
            return await call_next(request)
        
        # Validate API key (in production, check against database)
        # For now, we'll accept any non-empty API key
        if not api_key or len(api_key) < 10:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
            )
        
        # Store API key in request state for rate limiting
        request.state.api_key = api_key
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting per API key."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or rate limit error
        """
        # Skip rate limiting for docs and health endpoints
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get API key from request state (set by APIKeyMiddleware)
        api_key = getattr(request.state, "api_key", None)
        
        if not api_key:
            # Try to get from Authorization header for JWT tokens
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header.split(" ")[1][:20]  # Use first 20 chars as identifier
            else:
                # No API key, skip rate limiting (will be caught by auth middleware)
                return await call_next(request)
        
        # Check rate limit
        is_limited, current_count, remaining = rate_limit_store.is_rate_limited(api_key)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for API key: {api_key[:10]}...")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "limit": rate_limit_store._max_requests,
                    "window": f"{rate_limit_store._window_size}s",
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_store._max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + rate_limit_store._window_size)),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit_store._max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + rate_limit_store._window_size))
        
        return response


# Middleware factory functions
def api_key_middleware():
    """Create API key middleware instance."""
    return APIKeyMiddleware


def rate_limit_middleware():
    """Create rate limit middleware instance."""
    return RateLimitMiddleware
