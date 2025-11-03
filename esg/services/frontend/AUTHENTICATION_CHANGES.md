# Frontend Authentication Changes

## Overview

This document describes the changes made to the frontend to support unauthenticated access for read-only operations (GET requests) while requiring authentication only for mutation operations (POST/PUT/DELETE/PATCH).

## Changes Made

### 1. API Client Updates (`src/services/api.ts`)

#### Conditional Authentication Headers

The API client now conditionally includes authentication headers based on the HTTP method:

- **GET requests**: No authentication headers are sent
- **POST/PUT/DELETE/PATCH requests**: Authentication headers (Bearer token and API key) are included

**Implementation:**
```typescript
// Request interceptor for auth
this.client.interceptors.request.use(
  (config) => {
    // Only add auth headers for mutation operations (POST, PUT, DELETE, PATCH)
    const method = config.method?.toUpperCase()
    const isMutation = method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH'
    
    if (isMutation) {
      // Add auth token if available
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`
      }

      // Add API key from environment if available
      const apiKey = import.meta.env.VITE_API_KEY
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)
```

#### Enhanced Error Handling

The 401 error handler now distinguishes between mutation and read operations:

- **Mutation operations**: Clear auth token and throw authentication error
- **Read operations**: Throw error without clearing token (shouldn't happen for public endpoints)

**Implementation:**
```typescript
case 401:
  // Unauthorized - only clear token for mutation operations
  const method = originalRequest?.method?.toUpperCase()
  const isMutation = method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH'
  
  if (isMutation) {
    // Clear token and require authentication for mutations
    this.clearAuth()
    throw new ApiError('Authentication required for this operation', 401, data)
  } else {
    // For GET requests, this shouldn't happen but handle gracefully
    throw new ApiError('Authentication required', 401, data)
  }
```

### 2. New Components

#### AuthPrompt Component (`src/components/AuthPrompt.vue`)

A reusable modal component that prompts users to authenticate when attempting operations that require authentication.

**Features:**
- Modal overlay with lock icon
- Customizable message
- "Sign In" and "Cancel" buttons
- Emits events for parent component handling

**Usage:**
```vue
<AuthPrompt
  v-if="showAuthPrompt"
  message="You need to sign in to trigger report processing."
  @sign-in="handleSignIn"
  @cancel="showAuthPrompt = false"
/>
```

### 3. New Composables

#### useAuth Composable (`src/composables/useAuth.ts`)

A composable for managing authentication state and operations.

**Features:**
- Check authentication status
- Sign in/sign out operations (placeholder for future implementation)
- `canPerformMutation` computed property
- `requireAuth` wrapper for protected operations

**Usage:**
```typescript
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, canPerformMutation, requireAuth } = useAuth()

const handleMutationOperation = () => {
  if (!isAuthenticated.value) {
    showAuthPrompt.value = true
    return
  }
  
  // Perform the mutation operation
  performMutation()
}
```

## User Experience

### Read-Only Access (No Authentication Required)

Users can now:
- Browse companies without logging in
- View BRSR indicator definitions
- View company indicators and scores
- View reports and citations
- Search and filter companies

### Mutation Operations (Authentication Required)

When users attempt operations like:
- Triggering report processing
- Creating/updating/deleting data

They will see the `AuthPrompt` component with a clear message indicating authentication is required.

## Requirements Satisfied

- **3.1**: API client conditionally includes auth headers only for POST/PUT/DELETE operations
- **3.2**: Frontend displays company data without requiring user login
- **3.3**: Frontend displays indicator data without requiring user login
- **3.4**: Frontend displays score data without requiring user login
- **3.5**: Clear login prompt displayed when authentication is required

## Testing

### Manual Testing

1. **Test Read Operations Without Auth:**
   ```bash
   # Start the frontend
   cd services/frontend
   npm run dev
   
   # Navigate to http://localhost:3000
   # Browse companies, indicators, and scores without logging in
   ```

2. **Test Mutation Operations:**
   ```bash
   # Attempt to trigger report processing or other mutations
   # Should see AuthPrompt component
   ```

### Browser DevTools

Check the Network tab to verify:
- GET requests do not include `Authorization` or `X-API-Key` headers
- POST/PUT/DELETE requests include authentication headers (when available)

## Future Enhancements

1. **Implement Actual Authentication:**
   - Add login page/modal
   - Implement JWT token management
   - Add refresh token logic

2. **Add Protected Routes:**
   - Create admin dashboard routes
   - Add route guards for admin-only pages

3. **Enhance AuthPrompt:**
   - Add inline login form
   - Support OAuth providers
   - Remember redirect after login

## Migration Notes

### For Developers

- No breaking changes to existing components
- All existing GET requests will work without authentication
- Future mutation operations should use the `useAuth` composable to check authentication status

### For Users

- Existing functionality remains unchanged
- Users can now browse data without creating an account
- Authentication will only be required for data modification operations

## Related Files

- `services/frontend/src/services/api.ts` - API client with conditional auth
- `services/frontend/src/components/AuthPrompt.vue` - Authentication prompt component
- `services/frontend/src/composables/useAuth.ts` - Authentication composable
- `services/frontend/src/components/README.md` - Component documentation

## References

- Requirements: `.kiro/specs/system-integration-fixes/requirements.md` (Requirement 3)
- Design: `.kiro/specs/system-integration-fixes/design.md` (Section 2)
- Tasks: `.kiro/specs/system-integration-fixes/tasks.md` (Task 3)
