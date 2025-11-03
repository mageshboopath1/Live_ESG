#!/usr/bin/env python3
"""Demo script to show Redis caching in action."""

import time
from src.cache import cache_manager, cache_key
from src.config import settings

def main():
    """Demonstrate caching functionality."""
    print("=" * 60)
    print("Redis Caching Demo")
    print("=" * 60)
    
    # Check if cache is enabled
    print(f"\n1. Cache Status:")
    print(f"   Enabled: {cache_manager.enabled}")
    if cache_manager.enabled:
        print(f"   Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"   DB: {settings.REDIS_DB}")
    
    if not cache_manager.enabled:
        print("\n❌ Redis cache is not available. Please start Redis first.")
        return
    
    # Demo 1: Simple cache operations
    print(f"\n2. Simple Cache Operations:")
    key = cache_key("demo", "company", "1")
    data = {
        "id": 1,
        "name": "Reliance Industries",
        "symbol": "RELIANCE",
        "industry": "Oil & Gas"
    }
    
    print(f"   Setting cache: {key}")
    cache_manager.set(key, data, ttl=60)
    
    print(f"   Getting cache: {key}")
    cached = cache_manager.get(key)
    print(f"   ✓ Retrieved: {cached['name']}")
    
    # Demo 2: Cache with TTL
    print(f"\n3. Cache TTL Demo:")
    short_key = cache_key("demo", "short-lived")
    cache_manager.set(short_key, {"message": "This expires in 2 seconds"}, ttl=2)
    print(f"   Set cache with 2s TTL")
    
    print(f"   Immediate read: {cache_manager.get(short_key)}")
    print(f"   Waiting 3 seconds...")
    time.sleep(3)
    print(f"   After expiry: {cache_manager.get(short_key)}")
    
    # Demo 3: Pattern deletion
    print(f"\n4. Pattern-Based Deletion:")
    cache_manager.set(cache_key("demo", "company", "1", "data"), {"id": 1}, ttl=60)
    cache_manager.set(cache_key("demo", "company", "1", "scores"), {"score": 85}, ttl=60)
    cache_manager.set(cache_key("demo", "company", "2", "data"), {"id": 2}, ttl=60)
    print(f"   Created 3 cache entries")
    
    deleted = cache_manager.delete_pattern("demo:company:1*")
    print(f"   Deleted pattern 'demo:company:1*': {deleted} keys")
    
    print(f"   Checking remaining:")
    print(f"   - company:1:data: {cache_manager.get(cache_key('demo', 'company', '1', 'data'))}")
    print(f"   - company:2:data: {cache_manager.get(cache_key('demo', 'company', '2', 'data'))}")
    
    # Demo 4: Complex data structures
    print(f"\n5. Complex Data Structures:")
    complex_key = cache_key("demo", "score-breakdown")
    complex_data = {
        "company_id": 1,
        "year": 2024,
        "overall_score": 85.5,
        "pillars": [
            {
                "name": "Environmental",
                "score": 88.2,
                "indicators": [
                    {"code": "E1", "value": 100, "weight": 0.3},
                    {"code": "E2", "value": 85, "weight": 0.7}
                ]
            },
            {
                "name": "Social",
                "score": 82.1,
                "indicators": [
                    {"code": "S1", "value": 90, "weight": 0.5},
                    {"code": "S2", "value": 74, "weight": 0.5}
                ]
            }
        ]
    }
    
    cache_manager.set(complex_key, complex_data, ttl=60)
    cached_complex = cache_manager.get(complex_key)
    print(f"   Cached complex score breakdown")
    print(f"   ✓ Overall Score: {cached_complex['overall_score']}")
    print(f"   ✓ Pillars: {len(cached_complex['pillars'])}")
    print(f"   ✓ First Pillar: {cached_complex['pillars'][0]['name']} - {cached_complex['pillars'][0]['score']}")
    
    # Cleanup
    print(f"\n6. Cleanup:")
    cache_manager.delete_pattern("demo:*")
    print(f"   ✓ Cleaned up all demo cache entries")
    
    print(f"\n{'=' * 60}")
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
