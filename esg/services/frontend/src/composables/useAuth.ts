import { ref, computed } from 'vue'
import apiClient from '@/services/api'

/**
 * Composable for handling authentication state and operations
 */
export function useAuth() {
  const isAuthenticated = ref(false)
  const authToken = ref<string | null>(null)

  // Check if user has a valid auth token
  const checkAuth = () => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      authToken.value = token
      isAuthenticated.value = true
      return true
    }
    return false
  }

  // Sign in (placeholder for future implementation)
  const signIn = async (credentials: { username: string; password: string }) => {
    // Future: Implement actual authentication
    console.log('Sign in with:', credentials)
    throw new Error('Authentication not yet implemented')
  }

  // Sign out
  const signOut = () => {
    apiClient.clearAuth()
    authToken.value = null
    isAuthenticated.value = false
  }

  // Check if user can perform mutation operations
  const canPerformMutation = computed(() => isAuthenticated.value)

  // Require authentication for an operation
  const requireAuth = (operation: () => void | Promise<void>) => {
    return async () => {
      if (!isAuthenticated.value) {
        throw new Error('Authentication required for this operation')
      }
      return await operation()
    }
  }

  // Initialize auth state
  checkAuth()

  return {
    isAuthenticated,
    authToken,
    canPerformMutation,
    checkAuth,
    signIn,
    signOut,
    requireAuth
  }
}
