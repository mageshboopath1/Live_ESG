# API Gateway Endpoint Authentication Status

## Public Endpoints (No Authentication Required)

### Root & Health
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /redoc` - ReDoc documentation

### Companies
- `GET /api/companies` - List all companies
- `GET /api/companies/search` - Search companies
- `GET /api/companies/{company_id}` - Get company details

### Indicators
- `GET /api/indicators/definitions` - Get BRSR indicator definitions ✨ NEW
- `GET /api/companies/{company_id}/indicators` - List company indicators
- `GET /api/indicators/compare` - Compare indicators across companies
- `GET /api/indicators/{indicator_id}` - Get indicator details

### Scores
- `GET /api/companies/{company_id}/scores` - Get company ESG scores
- `GET /api/scores/breakdown/{company_id}/{year}` - Get detailed score breakdown

### Reports
- `GET /api/companies/{company_id}/reports` - List company reports
- `GET /api/reports/{object_key:path}` - Get report details

### Cache
- `GET /api/cache/status` - Get cache status

## Protected Endpoints (Authentication Required)

### Cache Management
- `POST /api/cache/invalidate/company/{company_id}` - Invalidate company cache
- `POST /api/cache/invalidate/indicators` - Invalidate indicators cache
- `POST /api/cache/invalidate/scores/{company_id}` - Invalidate scores cache
- `POST /api/cache/clear` - Clear all cache

### Reports
- `POST /api/reports/trigger-processing` - Trigger report processing

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/api-keys` - Create API key
- `DELETE /api/auth/api-keys/{key_id}` - Revoke API key
- `GET /api/auth/me` - Get current user
- `GET /api/auth/api-keys` - List user's API keys

## Authentication Methods

### For Protected Endpoints
1. **JWT Bearer Token**: Include in `Authorization` header
   ```
   Authorization: Bearer <jwt_token>
   ```

2. **API Key**: Include in `X-API-Key` header (if implemented)
   ```
   X-API-Key: <api_key>
   ```

## Response Codes

- `200 OK` - Successful request
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Valid authentication but insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

All endpoints are subject to rate limiting:
- **Limit**: 100 requests per minute per API key/token
- **Headers**: 
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets
