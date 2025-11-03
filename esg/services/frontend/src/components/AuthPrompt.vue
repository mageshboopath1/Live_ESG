<template>
  <div class="auth-prompt">
    <div class="auth-prompt-content">
      <div class="auth-prompt-icon">
        <svg class="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
          />
        </svg>
      </div>
      <h3 class="auth-prompt-title">Authentication Required</h3>
      <p class="auth-prompt-message">
        {{ message || 'You need to sign in to perform this action.' }}
      </p>
      <div class="auth-prompt-actions">
        <button @click="handleSignIn" class="btn-primary">
          Sign In
        </button>
        <button @click="handleCancel" class="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'sign-in'): void
  (e: 'cancel'): void
}>()

const handleSignIn = () => {
  emit('sign-in')
  // Future: Redirect to login page or open login modal
  console.log('Sign in requested')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.auth-prompt {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50;
}

.auth-prompt-content {
  @apply bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4;
  @apply transform transition-all;
}

.auth-prompt-icon {
  @apply flex justify-center mb-4;
}

.auth-prompt-title {
  @apply text-xl font-semibold text-gray-900 text-center mb-2;
}

.auth-prompt-message {
  @apply text-gray-600 text-center mb-6;
}

.auth-prompt-actions {
  @apply flex gap-3 justify-center;
}

.btn-primary {
  @apply px-6 py-2 bg-blue-600 text-white rounded-lg font-medium;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

.btn-secondary {
  @apply px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium;
  @apply hover:bg-gray-200 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2;
}
</style>
