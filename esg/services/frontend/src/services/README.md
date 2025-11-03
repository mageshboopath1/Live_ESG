# API Client Service

This directory contains the API client service for communicating with the ESG Intelligence Platform backend.

## Overview

The API client (`api.ts`) provides a typed, robust interface for all backend API endpoints with built-in:
- Authentication handling (JWT tokens and API keys)
- Automatic retry logic with exponential backoff
- Request/response interceptors
- Comprehensive error handling
- TypeScript type safety

## Usage

### Basic Import

```typescript
import apiClient from '@/services/api'
```

### Authentication

```typescript
// Set auth token (e.g., after login)
apiClient.setAuthToken('your-jwt-token')

// Clear auth (e.g., on logout)
apiClient.clearAuth()

// Auth token is automatically loaded from localStorage on initialization
```

### Company Endpoints

```typescript
// Get all companies with pagination
const { companies, total, page, limit } = await apiClient.getCompanies({
  page: 1,
  limit: 50,
  industry: 'Technology'
})

// Get single company
const company = await apiClient.getCompany(123)

// Search companies
const results = await apiClient.searchCompanies('Reliance')
```

### Report Endpoints

```typescript
// Get company reports
const reports = await apiClient.getCompanyReports(123)

// Get specific report
const report = await apiClient.getReport('RELIANCE/2024_BRSR.pdf')

// Trigger report processing
const result = await apiClient.triggerReportProcessing('RELIANCE/2024_BRSR.pdf')
```

### Indicator Endpoints

```typescript
// Get company indicators for a year
const indicators = await apiClient.getCompanyIndicators(123, 2024, {
  attribute: 1, // Optional: filter by BRSR attribute
  pillar: 'E'   // Optional: filter by pillar (E/S/G)
})

// Get single indicator with citations
const { indicator, definition, citations } = await apiClient.getIndicator(456)

// Compare indicators across companies
const comparison = await apiClient.compareIndicators([123, 456], 2024, 'GHG_SCOPE1')

// Get BRSR indicator definitions
const definitions = await apiClient.getBRSRIndicatorDefinitions()
```

### Score Endpoints

```typescript
// Get company ESG scores
const scores = await apiClient.getCompanyScores(123, 2024)

// Get detailed score breakdown
const breakdown = await apiClient.getScoreBreakdown(123, 2024)

// Get score history
const history = await apiClient.getScoreHistory(123, 2020, 2024)
```

### Citation Endpoints

```typescript
// Get citations for an indicator
const citations = await apiClient.getCitations(789)

// Get document page URL
const { url, presigned_url } = await apiClient.getDocumentPage(
  'RELIANCE/2024_BRSR.pdf',
  45
)

// Get full document URL
const { url, presigned_url } = await apiClient.getDocumentUrl('RELIANCE/2024_BRSR.pdf')
```

## Error Handling

The API client throws `ApiError` instances with detailed information:

```typescript
import { ApiError } from '@/services/api'

try {
  const company = await apiClient.getCompany(123)
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message)
    console.error('Status Code:', error.statusCode)
    console.error('Response:', error.response)
    
    // Handle specific errors
    if (error.statusCode === 404) {
      // Handle not found
    } else if (error.statusCode === 401) {
      // Handle unauthorized - redirect to login
    }
  }
}
```

## Retry Logic

The client automatically retries failed requests with exponential backoff for:
- Network errors
- Rate limit errors (429)
- Server errors (500, 502, 503, 504)

Configuration:
- Max retries: 3
- Initial delay: 1 second
- Backoff: Exponential (1s, 2s, 4s)

## Environment Variables

Configure the API client using environment variables:

```env
# API base URL (defaults to /api for proxy)
VITE_API_URL=http://localhost:8000

# Optional API key for authentication
VITE_API_KEY=your-api-key
```

## Interceptors

### Request Interceptor
- Adds `Authorization` header with JWT token if available
- Adds `X-API-Key` header if configured in environment

### Response Interceptor
- Handles authentication errors (401) - clears token
- Handles rate limiting (429) - retries with backoff
- Handles server errors (5xx) - retries with backoff
- Transforms errors into `ApiError` instances

## Type Safety

All API methods are fully typed using TypeScript interfaces from `@/types`:
- `Company`
- `Report`
- `BRSRIndicatorDefinition`
- `ExtractedIndicator`
- `Citation`
- `ESGScore`
- `ScoreBreakdown`

## Testing

The API client can be mocked in tests:

```typescript
import { vi } from 'vitest'
import apiClient from '@/services/api'

// Mock a method
vi.spyOn(apiClient, 'getCompanies').mockResolvedValue({
  companies: [/* mock data */],
  total: 1,
  page: 1,
  limit: 50
})
```

## Best Practices

1. **Always handle errors**: Wrap API calls in try-catch blocks
2. **Use TypeScript types**: Leverage the typed responses for type safety
3. **Implement loading states**: Show loading indicators during API calls
4. **Cache responses**: Use Pinia stores to cache frequently accessed data
5. **Debounce search**: Debounce search inputs to avoid excessive API calls
6. **Handle auth expiry**: Listen for 401 errors and redirect to login

## Example: Using in a Component

```typescript
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/services/api'
import type { Company } from '@/types'

const companies = ref<Company[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const fetchCompanies = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await apiClient.getCompanies({ page: 1, limit: 50 })
    companies.value = response.companies
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An error occurred'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCompanies()
})
</script>
```
