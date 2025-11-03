# Redis Caching Implementation

This document describes the Redis caching layer implemented in the API Gateway service.

## Overview

The API Gateway uses Redis for caching frequently accessed data to improve performance and reduce database load. The caching layer is designed to be:

- **Transparent**: Caching happens automatically without changing API contracts
- **Resilient**: The service continues to work if Redis is unavailable
- **Configurable**: TTL values and cache behavior can be configured via environment variables
- **Manageable**: Cache invalidation endpoints allow manual cache management

## Cached Data

### 1. Company Data (TTL: 1 hour)

**Cache Key Format**: `company:{company_id}`

**Endpoints**:
- `GET /api/companies/{company_id}` - Company details with report counts and available years

**Invalidation**:
- Automatic: When company data is updated
- Manual: `POST /api/cache/invalidate/company/{company_id}`

### 2. BRSR Indicator Definitions (TTL: 24 hours)

**Cache Key Format**: `indicators:definitions:all`

**Endpoints**:
- `GET /api/indicators/compare` - Uses cached indicator definitions for comparison

**Invalidation**:
- Manual: `POST /api/cache/invalidate/indicators`
- Use when indicator definitions are updated in the database

### 3. ESG Scores (TTL: 1 hour)

**Cache Key Format**: 
- `scores:{company_id}:{year}` - Individual scores
- `scores:breakdown:{company_id}:{year}` - Detailed score breakdown

**Endpoints**:
- `GET /api/companies/{company_id}/scores?year={year}` - Company scores
- `GET /api/scores/breakdown/{company_id}/{year}` - Detailed score breakdown

**Invalidation**:
- Automatic: When scores are recalculated
- Manual: `POST /api/cache/invalidate/scores/{company_id}?year={year}`

## Configuration

### Environment Variables

```bash
# Redis Connection
REDIS_HOST=redis              # Redis server hostname
REDIS_PORT=6379               # Redis server port
REDIS_DB=0                    # Redis database number
REDIS_PASSWORD=               # Redis password (optional)
REDIS_ENABLED=true            # Enable/disable caching

# Cache TTL (in seconds)
CACHE_TTL_COMPANY=3600        # 1 hour
CACHE_TTL_INDICATORS=86400    # 24 hours
CACHE_TTL_SCORES=3600         # 1 hour
```

### Docker Compose

Redis is included in the docker-compose configuration:

```yaml
redis:
  image: redis:7-alpine
  container_name: esg-redis
  restart: always
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  command: redis-server --appendonly yes
  networks:
    - backend
```

## Cache Management API

### Get Cache Status

```bash
GET /api/cache/status
```

Returns cache configuration and status.

### Invalidate Company Cache

```bash
POST /api/cache/invalidate/company/{company_id}
```

Invalidates all cached data for a specific company (details, indicators, scores).

### Invalidate Indicator Definitions

```bash
POST /api/cache/invalidate/indicators
```

Invalidates cached BRSR indicator definitions.

### Invalidate Scores

```bash
POST /api/cache/invalidate/scores/{company_id}?year={year}
```

Invalidates score cache for a company. If `year` is not specified, invalidates all years.

### Clear All Cache

```bash
POST /api/cache/clear
```

**WARNING**: Clears the entire cache. Use with caution.

## Implementation Details

### Cache Manager

The `CacheManager` class in `src/cache.py` provides:

- Connection pooling with automatic reconnection
- Health checks to detect Redis availability
- Graceful degradation when Redis is unavailable
- JSON serialization/deserialization
- Pattern-based key deletion

### Cache Keys

Cache keys follow a hierarchical structure:

```
{resource}:{id}:{sub-resource}
```

Examples:
- `company:1` - Company with ID 1
- `scores:1:2024` - Scores for company 1 in year 2024
- `scores:breakdown:1:2024` - Score breakdown for company 1 in year 2024
- `indicators:definitions:all` - All BRSR indicator definitions

### Automatic Invalidation

Cache invalidation functions are provided for use when data is updated:

```python
from src.cache import (
    invalidate_company_cache,
    invalidate_indicators_cache,
    invalidate_scores_cache
)

# After updating company data
invalidate_company_cache(company_id)

# After updating indicator definitions
invalidate_indicators_cache()

# After recalculating scores
invalidate_scores_cache(company_id, year)
```

## Performance Impact

### Expected Improvements

- **Company Details**: ~50-100ms reduction per request
- **Indicator Definitions**: ~100-200ms reduction for comparison queries
- **Score Breakdown**: ~200-500ms reduction per request (complex queries)

### Cache Hit Rates

Monitor cache effectiveness using Redis INFO command:

```bash
docker exec esg-redis redis-cli INFO stats
```

Look for:
- `keyspace_hits` - Number of successful cache lookups
- `keyspace_misses` - Number of cache misses
- Hit rate = hits / (hits + misses)

Target hit rate: >80% for optimal performance

## Monitoring

### Health Check

The `/health` endpoint includes cache status:

```json
{
  "status": "healthy",
  "service": "api-gateway",
  "database": "connected",
  "cache": "enabled"
}
```

### Logs

Cache operations are logged at DEBUG level:

```
Cache hit: company:1
Cache miss: scores:2:2024
Cache set: company:1 (TTL: 3600s)
Cache delete pattern 'company:1*': 3 keys
```

## Troubleshooting

### Cache Not Working

1. Check Redis is running:
   ```bash
   docker ps | grep redis
   ```

2. Check Redis connectivity:
   ```bash
   docker exec esg-redis redis-cli ping
   ```

3. Check API Gateway logs for Redis connection errors

4. Verify environment variables are set correctly

### Cache Disabled

If Redis is unavailable, the service automatically disables caching and continues to work normally. Check logs for:

```
Redis connection failed, caching disabled: [error details]
Redis cache disabled - running without caching
```

### Stale Data

If you see stale data, manually invalidate the cache:

```bash
# Invalidate specific company
curl -X POST http://localhost:8000/api/cache/invalidate/company/1

# Clear all cache
curl -X POST http://localhost:8000/api/cache/clear
```

## Testing

Run cache tests:

```bash
# Start Redis first
docker-compose up -d redis

# Run tests
cd services/api-gateway
uv run pytest test_cache.py -v
```

Tests include:
- Cache key generation
- Basic cache operations (set, get, delete)
- Pattern-based deletion
- Complex data structures
- Graceful degradation when disabled

## Best Practices

1. **TTL Selection**: Choose TTL based on data update frequency
   - Frequently updated: 5-15 minutes
   - Occasionally updated: 1 hour
   - Rarely updated: 24 hours

2. **Cache Invalidation**: Always invalidate cache when data is updated
   - Use provided invalidation functions
   - Consider invalidating related data

3. **Cache Keys**: Use consistent, hierarchical key naming
   - Include resource type and identifiers
   - Use colons as separators

4. **Error Handling**: Cache operations should never break the API
   - All cache operations have try-catch blocks
   - Service continues without caching if Redis fails

5. **Monitoring**: Regularly check cache hit rates and adjust TTLs accordingly
