# API Gateway Authentication Changes

## Summary

Successfully implemented task 2 "Fix API Gateway Authentication for Public Endpoints" from the system integration fixes specification. The API Gateway now allows public access to GET endpoints while requiring authentication only for POST/PUT/DELETE operations.

## Changes Made

### 1. Removed Global Authentication Middleware

**File**: `services/api-gateway/src/main.py`

- Removed the global `APIKeyMiddleware` that was requiring authentication for all endpoints
- Added comment explaining that authentication is now applied per-router
- GET operations are now public by default

### 2. Updated Routers with Selective Authentication

#### Cache Router (`services/api-gateway/src/routers/cache.py`)
- Added `require_auth` dependency to all POST endpoints:
  - `POST /api/cache/invalidate/company/{company_id}`
  - `POST /api/cache/invalidate/indicators`
  - `POST /api/cache/invalidate/scores/{company_id}`
  - `POST /api/cache/clear`
- GET endpoint `/api/cache/status` remains public

#### Reports Router (`services/api-gateway/src/routers/reports.py`)
- Added `require_auth` dependency to POST endpoint:
  - `POST /api/reports/trigger-processing`
- All GET endpoints remain public:
  - `GET /api/companies/{company_id}/reports`
  - `GET /api/reports/{object_key:path}`

#### Indicators Router (`services/api-gateway/src/routers/indicators.py`)
- Added new public GET endpoint:
  - `GET /api/indicators/definitions` - Returns all BRSR indicator definitions
  - Supports filtering by attribute and pillar
  - Uses caching for performance
- All existing GET endpoints remain public:
  - `GET /api/companies/{company_id}/indicators`
  - `GET /api/indicators/compare`
  - `GET /api/indicators/{indicator_id}`

#### Companies Router (`services/api-gateway/src/routers/companies.py`)
- No changes needed - already has only public GET endpoints

#### Scores Router (`services/api-gateway/src/routers/scores.py`)
- No changes needed - already has only public GET endpoints

## Authentication Behavior

### Public Endpoints (No Authentication Required)
- All GET requests to:
  - `/api/companies/*`
  - `/api/indicators/*`
  - `/api/scores/*`
  - `/api/reports/*` (except trigger-processing)
  - `/api/cache/status`
- Root endpoints: `/`, `/health`, `/docs`, `/redoc`

### Protected Endpoints (Authentication Required)
- All POST/PUT/DELETE requests
- Cache management operations
- Report processing triggers
- Auth-related endpoints (handled by auth router)

## Testing

Created `test_public_endpoints.py` to verify:
1. ✅ Public GET endpoints are accessible without authentication
2. ✅ Protected POST endpoints require authentication (return 401/403)
3. ✅ Database connectivity works for public endpoints
4. ✅ New `/api/indicators/definitions` endpoint works correctly

## Benefits

1. **Improved User Experience**: Users can browse ESG data without creating an account
2. **Simplified Frontend**: Frontend doesn't need to handle authentication for read-only operations
3. **Better Security**: Mutations still require authentication
4. **API Transparency**: Indicator definitions are publicly accessible for transparency

## Requirements Satisfied

- ✅ Requirement 2.1: API Gateway allows unauthenticated access to GET /api/companies endpoints
- ✅ Requirement 2.2: API Gateway allows unauthenticated access to GET /api/indicators endpoints
- ✅ Requirement 2.3: API Gateway allows unauthenticated access to GET /api/scores endpoints
- ✅ Requirement 2.4: API Gateway allows unauthenticated access to GET /api/reports endpoints
- ✅ Requirement 2.5: API Gateway requires authentication only for POST, PUT, DELETE operations

## Next Steps

The frontend should be updated (Task 3) to:
1. Remove authentication headers from GET requests
2. Only send authentication headers for POST/PUT/DELETE operations
3. Display login prompt only when attempting mutations
