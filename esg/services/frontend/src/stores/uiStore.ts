import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}

export interface Modal {
  id: string
  title: string
  content: string | null
  component?: string
  props?: Record<string, any>
  onClose?: () => void
}

export interface LoadingState {
  [key: string]: boolean
}

export const useUIStore = defineStore('ui', () => {
  // State
  const sidebarOpen = ref(true)
  const modals = ref<Modal[]>([])
  const toasts = ref<Toast[]>([])
  const loadingStates = ref<LoadingState>({})
  const globalLoading = ref(false)
  const globalError = ref<string | null>(null)
  const theme = ref<'light' | 'dark'>('light')

  // Computed
  const activeModal = computed(() => {
    return modals.value.length > 0 ? modals.value[modals.value.length - 1] : null
  })

  const hasActiveModal = computed(() => modals.value.length > 0)

  const isLoading = computed(() => {
    return globalLoading.value || Object.values(loadingStates.value).some((state) => state)
  })

  // Sidebar actions
  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
  }

  const setSidebarOpen = (open: boolean) => {
    sidebarOpen.value = open
  }

  // Modal actions
  const openModal = (modal: Omit<Modal, 'id'>) => {
    const id = `modal-${Date.now()}-${Math.random()}`
    modals.value.push({ ...modal, id })
    return id
  }

  const closeModal = (id?: string) => {
    if (id) {
      const index = modals.value.findIndex((m) => m.id === id)
      if (index >= 0) {
        const modal = modals.value[index]
        modal.onClose?.()
        modals.value.splice(index, 1)
      }
    } else {
      // Close the topmost modal
      const modal = modals.value.pop()
      modal?.onClose?.()
    }
  }

  const closeAllModals = () => {
    modals.value.forEach((modal) => modal.onClose?.())
    modals.value = []
  }

  // Toast actions
  const showToast = (
    message: string,
    type: 'success' | 'error' | 'info' | 'warning' = 'info',
    duration = 3000
  ) => {
    const id = `toast-${Date.now()}-${Math.random()}`
    const toast: Toast = { id, message, type, duration }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  const removeToast = (id: string) => {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index >= 0) {
      toasts.value.splice(index, 1)
    }
  }

  const clearToasts = () => {
    toasts.value = []
  }

  // Convenience toast methods
  const showSuccess = (message: string, duration = 3000) => {
    return showToast(message, 'success', duration)
  }

  const showError = (message: string, duration = 5000) => {
    return showToast(message, 'error', duration)
  }

  const showInfo = (message: string, duration = 3000) => {
    return showToast(message, 'info', duration)
  }

  const showWarning = (message: string, duration = 4000) => {
    return showToast(message, 'warning', duration)
  }

  // Loading state actions
  const setLoading = (key: string, loading: boolean) => {
    if (loading) {
      loadingStates.value[key] = true
    } else {
      delete loadingStates.value[key]
    }
  }

  const setGlobalLoading = (loading: boolean) => {
    globalLoading.value = loading
  }

  const clearLoadingStates = () => {
    loadingStates.value = {}
  }

  // Error handling
  const setGlobalError = (error: string | null) => {
    globalError.value = error
    if (error) {
      showError(error)
    }
  }

  const clearGlobalError = () => {
    globalError.value = null
  }

  // Theme actions
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    
    // Apply theme to document
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  const loadTheme = () => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    }
  }

  // Initialize theme on store creation
  loadTheme()

  return {
    // State
    sidebarOpen,
    modals,
    toasts,
    loadingStates,
    globalLoading,
    globalError,
    theme,
    
    // Computed
    activeModal,
    hasActiveModal,
    isLoading,
    
    // Sidebar actions
    toggleSidebar,
    setSidebarOpen,
    
    // Modal actions
    openModal,
    closeModal,
    closeAllModals,
    
    // Toast actions
    showToast,
    removeToast,
    clearToasts,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    
    // Loading actions
    setLoading,
    setGlobalLoading,
    clearLoadingStates,
    
    // Error actions
    setGlobalError,
    clearGlobalError,
    
    // Theme actions
    setTheme,
    toggleTheme,
    loadTheme
  }
})
