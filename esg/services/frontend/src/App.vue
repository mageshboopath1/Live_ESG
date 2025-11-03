<template>
  <div id="app" class="min-h-screen bg-dark-bg flex flex-col">
    <!-- Toast Notifications -->
    <ToastNotification />

    <!-- Global Loading Overlay -->
    <LoadingSpinner
      v-if="uiStore.globalLoading"
      fullscreen
      size="lg"
      message="Loading..."
    />

    <!-- Sidebar -->
    <Sidebar
      :active-section="currentSection"
      @action="handleSidebarAction"
    />

    <!-- Header -->
    <AppHeader />

    <!-- Main Content -->
    <main
      :class="[
        'flex-1 transition-all duration-300',
        uiStore.sidebarOpen ? 'md:ml-20' : 'ml-0'
      ]"
    >
      <ErrorBoundary>
        <RouterView v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </ErrorBoundary>
    </main>

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onErrorCaptured } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useUIStore } from '@/stores/uiStore'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import Sidebar from '@/components/Sidebar.vue'
import ToastNotification from '@/components/ToastNotification.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const router = useRouter()
const uiStore = useUIStore()

// Track current active section for sidebar
const currentSection = ref<'favorite' | 'calendar' | 'insights' | 'settings' | 'add' | undefined>(undefined)

// Handle sidebar actions
const handleSidebarAction = (actionType: 'favorite' | 'calendar' | 'insights' | 'settings' | 'add') => {
  currentSection.value = actionType
  
  // Handle different actions
  switch (actionType) {
    case 'favorite':
      uiStore.showInfo('Favorites feature coming soon')
      break
    case 'calendar':
      uiStore.showInfo('Calendar feature coming soon')
      break
    case 'insights':
      uiStore.showInfo('Insights feature coming soon')
      break
    case 'settings':
      uiStore.showInfo('Settings feature coming soon')
      break
    case 'add':
      uiStore.showInfo('Add new feature coming soon')
      break
  }
}

onMounted(() => {
  // Load theme preference
  uiStore.loadTheme()
})

// Global error handler
onErrorCaptured((err: Error) => {
  console.error('Global error:', err)
  uiStore.showError(err.message || 'An unexpected error occurred')
  
  // Navigate to error page for critical errors
  if (err.message.includes('Failed to fetch') || err.message.includes('Network')) {
    router.push({
      name: 'error',
      query: { message: 'Network error. Please check your connection.' }
    })
  }
  
  return false
})

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  uiStore.showError('An unexpected error occurred')
  event.preventDefault()
})
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Page transition animations */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive utilities */
@media (max-width: 768px) {
  #app {
    font-size: 14px;
  }
}

/* Focus styles for accessibility */
*:focus-visible {
  outline: 2px solid #a8e63d;
  outline-offset: 2px;
}

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}
</style>
