"""Tests for Redis caching functionality."""

import pytest
from src.cache import CacheManager, cache_key


def test_cache_key_generation():
    """Test cache key generation."""
    key = cache_key("company", "1")
    assert key == "company:1"
    
    key = cache_key("scores", "1", "2024")
    assert key == "scores:1:2024"
    
    key = cache_key("indicators", "definitions", "all")
    assert key == "indicators:definitions:all"


def test_cache_manager_initialization():
    """Test cache manager initialization."""
    cache_mgr = CacheManager()
    
    # Cache manager should initialize (may be disabled if Redis not available)
    assert cache_mgr is not None
    assert isinstance(cache_mgr.enabled, bool)


def test_cache_set_get_delete():
    """Test basic cache operations."""
    cache_mgr = CacheManager()
    
    if not cache_mgr.enabled:
        pytest.skip("Redis not available, skipping cache tests")
    
    # Test set and get
    test_key = "test:key:1"
    test_value = {"id": 1, "name": "Test Company", "score": 85.5}
    
    result = cache_mgr.set(test_key, test_value, ttl=60)
    assert result is True
    
    cached_value = cache_mgr.get(test_key)
    assert cached_value is not None
    assert cached_value["id"] == 1
    assert cached_value["name"] == "Test Company"
    assert cached_value["score"] == 85.5
    
    # Test delete
    result = cache_mgr.delete(test_key)
    assert result is True
    
    cached_value = cache_mgr.get(test_key)
    assert cached_value is None


def test_cache_pattern_delete():
    """Test pattern-based cache deletion."""
    cache_mgr = CacheManager()
    
    if not cache_mgr.enabled:
        pytest.skip("Redis not available, skipping cache tests")
    
    # Set multiple keys
    cache_mgr.set("company:1:data", {"id": 1}, ttl=60)
    cache_mgr.set("company:1:scores", {"score": 85}, ttl=60)
    cache_mgr.set("company:2:data", {"id": 2}, ttl=60)
    
    # Delete pattern
    deleted = cache_mgr.delete_pattern("company:1*")
    assert deleted >= 2
    
    # Verify deletion
    assert cache_mgr.get("company:1:data") is None
    assert cache_mgr.get("company:1:scores") is None
    assert cache_mgr.get("company:2:data") is not None
    
    # Cleanup
    cache_mgr.delete("company:2:data")


def test_cache_with_complex_data():
    """Test caching with complex nested data structures."""
    cache_mgr = CacheManager()
    
    if not cache_mgr.enabled:
        pytest.skip("Redis not available, skipping cache tests")
    
    test_key = "test:complex:data"
    complex_data = {
        "company_id": 1,
        "scores": {
            "environmental": 85.5,
            "social": 90.2,
            "governance": 78.3
        },
        "indicators": [
            {"id": 1, "value": 100, "confidence": 0.95},
            {"id": 2, "value": 200, "confidence": 0.88}
        ],
        "metadata": {
            "calculated_at": "2024-01-01T00:00:00",
            "version": "1.0"
        }
    }
    
    cache_mgr.set(test_key, complex_data, ttl=60)
    cached = cache_mgr.get(test_key)
    
    assert cached is not None
    assert cached["company_id"] == 1
    assert cached["scores"]["environmental"] == 85.5
    assert len(cached["indicators"]) == 2
    assert cached["indicators"][0]["confidence"] == 0.95
    
    # Cleanup
    cache_mgr.delete(test_key)


def test_cache_disabled_gracefully():
    """Test that cache operations fail gracefully when disabled."""
    # Create a cache manager with Redis disabled
    cache_mgr = CacheManager()
    cache_mgr._enabled = False
    cache_mgr._client = None
    
    # All operations should return None/False without errors
    assert cache_mgr.get("any:key") is None
    assert cache_mgr.set("any:key", {"data": "value"}, ttl=60) is False
    assert cache_mgr.delete("any:key") is False
    assert cache_mgr.delete_pattern("any:*") == 0
    assert cache_mgr.clear_all() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
