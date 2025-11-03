<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="not-found-icon">
        <svg class="w-24 h-24 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h1 class="not-found-title">404</h1>
      <h2 class="not-found-subtitle">Page Not Found</h2>
      <p class="not-found-message">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div class="not-found-actions">
        <router-link to="/" class="btn-primary">
          Go to Home
        </router-link>
        <button @click="goBack" class="btn-secondary">
          Go Back
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.not-found-container {
  min-height: calc(100vh - 4rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.not-found-content {
  max-width: 32rem;
  width: 100%;
  text-align: center;
  background: white;
  padding: 3rem 2rem;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.not-found-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.not-found-title {
  font-size: 6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 1rem;
}

.not-found-subtitle {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.75rem;
}

.not-found-message {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 2rem;
}

.not-found-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  transition: transform 0.2s, box-shadow 0.2s;
  text-decoration: none;
  display: inline-block;
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
  cursor: pointer;
}

.btn-secondary:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

@media (max-width: 640px) {
  .not-found-title {
    font-size: 4rem;
  }

  .not-found-subtitle {
    font-size: 1.5rem;
  }

  .not-found-content {
    padding: 2rem 1.5rem;
  }
}
</style>
