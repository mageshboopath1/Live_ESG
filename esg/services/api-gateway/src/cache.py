"""Redis caching utilities for API Gateway."""

import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
import redis
from redis.exceptions import RedisError

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager with connection pooling."""

    def __init__(self):
        """Initialize Redis connection pool."""
        self._client: Optional[redis.Redis] = None
        self._enabled = settings.REDIS_ENABLED
        
        if self._enabled:
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self._client.ping()
                logger.info(f"Redis cache connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except RedisError as e:
                logger.warning(f"Redis connection failed, caching disabled: {e}")
                self._enabled = False
                self._client = None
    
    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled and self._client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or error
        """
        if not self.enabled:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self._client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "company:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.debug(f"Cache delete pattern '{pattern}': {deleted} keys")
                return deleted
            return 0
        except RedisError as e:
            logger.warning(f"Cache delete pattern error for '{pattern}': {e}")
            return 0
    
    def clear_all(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self._client.flushdb()
            logger.info("Cache cleared")
            return True
        except RedisError as e:
            logger.warning(f"Cache clear error: {e}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except RedisError as e:
                logger.warning(f"Error closing Redis connection: {e}")


# Global cache manager instance
cache_manager = CacheManager()


def cache_key(*parts: str) -> str:
    """
    Generate a cache key from parts.
    
    Args:
        *parts: Key parts to join
        
    Returns:
        Cache key string
        
    Example:
        cache_key("company", "1") -> "company:1"
        cache_key("scores", "1", "2024") -> "scores:1:2024"
    """
    return ":".join(str(part) for part in parts)


def cached(key_prefix: str, ttl: int, key_builder: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from function args
        
    Example:
        @cached("company", ttl=3600, key_builder=lambda company_id: f"company:{company_id}")
        def get_company(company_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default: use function name and args
                arg_str = "_".join(str(arg) for arg in args)
                kwarg_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = cache_key(key_prefix, func.__name__, arg_str, kwarg_str)
            
            # Try to get from cache
            cached_value = cache_manager.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_company_cache(company_id: int):
    """
    Invalidate all cache entries for a specific company.
    
    Args:
        company_id: Company ID
    """
    patterns = [
        f"company:{company_id}*",
        f"indicators:{company_id}*",
        f"scores:{company_id}*",
    ]
    
    for pattern in patterns:
        cache_manager.delete_pattern(pattern)
    
    logger.info(f"Invalidated cache for company_id={company_id}")


def invalidate_indicators_cache():
    """Invalidate all indicator definition cache entries."""
    cache_manager.delete_pattern("indicators:definitions*")
    logger.info("Invalidated indicator definitions cache")


def invalidate_scores_cache(company_id: int, year: Optional[int] = None):
    """
    Invalidate score cache entries for a company.
    
    Args:
        company_id: Company ID
        year: Optional specific year to invalidate
    """
    if year:
        cache_manager.delete(cache_key("scores", company_id, year))
        cache_manager.delete(cache_key("scores:breakdown", company_id, year))
    else:
        cache_manager.delete_pattern(f"scores:{company_id}*")
    
    logger.info(f"Invalidated scores cache for company_id={company_id}, year={year}")
