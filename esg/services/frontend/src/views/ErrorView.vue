<template>
  <div class="error-view-container">
    <div class="error-view-content">
      <div class="error-view-icon">
        <svg class="w-24 h-24 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h1 class="error-view-title">Oops!</h1>
      <h2 class="error-view-subtitle">Something went wrong</h2>
      <p class="error-view-message">
        {{ errorMessage || 'An unexpected error occurred. Please try again later.' }}
      </p>
      <div v-if="showDetails && errorDetails" class="error-view-details">
        <details>
          <summary class="cursor-pointer text-sm text-gray-600 hover:text-gray-900 font-medium">
            Show technical details
          </summary>
          <pre class="error-view-stack">{{ errorDetails }}</pre>
        </details>
      </div>
      <div class="error-view-actions">
        <button @click="retry" class="btn-primary">
          Try Again
        </button>
        <router-link to="/" class="btn-secondary">
          Go to Home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const errorMessage = ref('')
const errorDetails = ref('')
const showDetails = ref(import.meta.env.DEV)

onMounted(() => {
  // Get error from route params or query
  errorMessage.value = (route.params.message as string) || (route.query.message as string) || ''
  errorDetails.value = (route.params.details as string) || (route.query.details as string) || ''
})

const retry = () => {
  // Go back to previous page
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.error-view-container {
  min-height: calc(100vh - 4rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.error-view-content {
  max-width: 36rem;
  width: 100%;
  text-align: center;
  background: white;
  padding: 3rem 2rem;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.error-view-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.error-view-title {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 1rem;
}

.error-view-subtitle {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.75rem;
}

.error-view-message {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.error-view-details {
  margin-bottom: 2rem;
  text-align: left;
}

.error-view-stack {
  margin-top: 0.75rem;
  padding: 1rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  color: #374151;
  overflow-x: auto;
  max-height: 200px;
  font-family: 'Courier New', monospace;
}

.error-view-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  transition: transform 0.2s, box-shadow 0.2s;
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background-color: white;
  color: #374151;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-block;
}

.btn-secondary:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

@media (max-width: 640px) {
  .error-view-title {
    font-size: 2rem;
  }

  .error-view-subtitle {
    font-size: 1.5rem;
  }

  .error-view-content {
    padding: 2rem 1.5rem;
  }
}
</style>
