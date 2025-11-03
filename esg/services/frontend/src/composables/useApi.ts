import { ref } from 'vue'
import { ApiError } from '@/services/api'

/**
 * Generic composable for API calls with loading and error states
 */
export function useApi<T>(apiCall: () => Promise<T>) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const execute = async () => {
    loading.value = true
    error.value = null

    try {
      data.value = await apiCall()
      return data.value
    } catch (err) {
      if (err instanceof ApiError) {
        error.value = err.message
      } else if (err instanceof Error) {
        error.value = err.message
      } else {
        error.value = 'An unexpected error occurred'
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  const reset = () => {
    data.value = null
    error.value = null
    loading.value = false
  }

  return {
    data,
    loading,
    error,
    execute,
    reset
  }
}

/**
 * Example usage in a component:
 * 
 * const { data: companies, loading, error, execute } = useApi(() => 
 *   apiClient.getCompanies({ page: 1, limit: 50 })
 * )
 * 
 * onMounted(() => {
 *   execute()
 * })
 */
