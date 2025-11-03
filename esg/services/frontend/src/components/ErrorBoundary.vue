<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">
        <svg class="w-16 h-16 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h2 class="error-title">Something went wrong</h2>
      <p class="error-message">{{ errorMessage }}</p>
      <div v-if="showDetails && errorDetails" class="error-details">
        <details>
          <summary class="cursor-pointer text-sm text-gray-600 hover:text-gray-900">
            Show error details
          </summary>
          <pre class="error-stack">{{ errorDetails }}</pre>
        </details>
      </div>
      <div class="error-actions">
        <button @click="retry" class="btn-primary">
          Try Again
        </button>
        <button @click="goHome" class="btn-secondary">
          Go to Home
        </button>
      </div>
    </div>
  </div>
  <slot v-else></slot>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  showDetails?: boolean
}

withDefaults(defineProps<Props>(), {
  showDetails: import.meta.env.DEV
})

const router = useRouter()
const hasError = ref(false)
const errorMessage = ref('')
const errorDetails = ref('')

onErrorCaptured((err: Error) => {
  hasError.value = true
  errorMessage.value = err.message || 'An unexpected error occurred'
  errorDetails.value = err.stack || ''
  
  console.error('Error caught by boundary:', err)
  
  // Return false to prevent error from propagating
  return false
})

const retry = () => {
  hasError.value = false
  errorMessage.value = ''
  errorDetails.value = ''
}

const goHome = () => {
  hasError.value = false
  errorMessage.value = ''
  errorDetails.value = ''
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.error-container {
  max-width: 32rem;
  width: 100%;
  text-align: center;
}

.error-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.75rem;
}

.error-message {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.error-details {
  margin-bottom: 1.5rem;
  text-align: left;
}

.error-stack {
  margin-top: 0.5rem;
  padding: 1rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  color: #374151;
  overflow-x: auto;
  max-height: 200px;
}

.error-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background-color: #3b82f6;
  color: white;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 0.875rem;
  transition: background-color 0.2s;
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s;
  cursor: pointer;
}

.btn-secondary:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}
</style>
