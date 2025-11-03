<template>
  <div class="loading-spinner-container" :class="containerClass">
    <div class="loading-spinner" :class="sizeClass">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <p v-if="message" class="loading-message" :class="messageClass">
      {{ message }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  message?: string
  fullscreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  message: '',
  fullscreen: false
})

const containerClass = computed(() => ({
  'loading-fullscreen': props.fullscreen,
  'loading-inline': !props.fullscreen
}))

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'spinner-sm'
    case 'lg':
      return 'spinner-lg'
    default:
      return 'spinner-md'
  }
})

const messageClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs'
    case 'lg':
      return 'text-lg'
    default:
      return 'text-sm'
  }
})
</script>

<style scoped>
.loading-spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.loading-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.loading-inline {
  padding: 2rem;
}

.loading-spinner {
  position: relative;
  display: inline-block;
}

.spinner-sm {
  width: 24px;
  height: 24px;
}

.spinner-md {
  width: 48px;
  height: 48px;
}

.spinner-lg {
  width: 64px;
  height: 64px;
}

.spinner-ring {
  position: absolute;
  border: 3px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-sm .spinner-ring {
  border-width: 2px;
}

.spinner-lg .spinner-ring {
  border-width: 4px;
}

.spinner-ring:nth-child(1) {
  width: 100%;
  height: 100%;
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  animation-delay: -0.3s;
  border-top-color: #10b981;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  animation-delay: -0.15s;
  border-top-color: #8b5cf6;
}

.spinner-ring:nth-child(4) {
  width: 40%;
  height: 40%;
  top: 30%;
  left: 30%;
  border-top-color: #f59e0b;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-message {
  color: #6b7280;
  font-weight: 500;
  text-align: center;
}
</style>
