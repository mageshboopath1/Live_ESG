<template>
  <div class="example-container">
    <h2 class="text-2xl font-bold mb-6">AuthPrompt Component Example</h2>
    
    <div class="space-y-4">
      <!-- Example 1: Trigger Report Processing -->
      <div class="example-card">
        <h3 class="text-lg font-semibold mb-2">Example 1: Trigger Report Processing</h3>
        <p class="text-gray-600 mb-4">
          This button attempts a mutation operation. If not authenticated, it shows the auth prompt.
        </p>
        <button @click="handleTriggerProcessing" class="btn-primary">
          Trigger Report Processing
        </button>
      </div>

      <!-- Example 2: Create Company -->
      <div class="example-card">
        <h3 class="text-lg font-semibold mb-2">Example 2: Create Company</h3>
        <p class="text-gray-600 mb-4">
          This button attempts to create a new company. Requires authentication.
        </p>
        <button @click="handleCreateCompany" class="btn-primary">
          Create New Company
        </button>
      </div>

      <!-- Example 3: View Data (No Auth Required) -->
      <div class="example-card">
        <h3 class="text-lg font-semibold mb-2">Example 3: View Data (No Auth Required)</h3>
        <p class="text-gray-600 mb-4">
          This button fetches data using GET request. No authentication required.
        </p>
        <button @click="handleViewCompanies" class="btn-secondary">
          View Companies
        </button>
        <div v-if="companies.length > 0" class="mt-4">
          <p class="text-sm text-gray-600">Loaded {{ companies.length }} companies</p>
        </div>
      </div>

      <!-- Authentication Status -->
      <div class="example-card bg-blue-50">
        <h3 class="text-lg font-semibold mb-2">Authentication Status</h3>
        <div class="flex items-center gap-2">
          <span class="font-medium">Status:</span>
          <span
            class="px-3 py-1 rounded-full text-sm font-medium"
            :class="isAuthenticated ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
          >
            {{ isAuthenticated ? 'Authenticated' : 'Not Authenticated' }}
          </span>
        </div>
        <div class="mt-4 space-x-2">
          <button
            v-if="!isAuthenticated"
            @click="simulateLogin"
            class="btn-primary"
          >
            Simulate Login
          </button>
          <button
            v-else
            @click="handleSignOut"
            class="btn-secondary"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>

    <!-- Auth Prompt Modal -->
    <AuthPrompt
      v-if="showAuthPrompt"
      :message="authPromptMessage"
      @sign-in="handleSignIn"
      @cancel="showAuthPrompt = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AuthPrompt from './AuthPrompt.vue'
import { useAuth } from '@/composables/useAuth'
import apiClient from '@/services/api'
import type { Company } from '@/types'

const { isAuthenticated, signOut } = useAuth()
const showAuthPrompt = ref(false)
const authPromptMessage = ref('')
const companies = ref<Company[]>([])

// Example 1: Trigger Report Processing (requires auth)
const handleTriggerProcessing = () => {
  if (!isAuthenticated.value) {
    authPromptMessage.value = 'You need to sign in to trigger report processing.'
    showAuthPrompt.value = true
    return
  }
  
  console.log('Triggering report processing...')
  // apiClient.triggerReportProcessing('some-object-key')
}

// Example 2: Create Company (requires auth)
const handleCreateCompany = () => {
  if (!isAuthenticated.value) {
    authPromptMessage.value = 'You need to sign in to create a new company.'
    showAuthPrompt.value = true
    return
  }
  
  console.log('Creating company...')
  // apiClient.createCompany({ name: 'New Company' })
}

// Example 3: View Companies (no auth required)
const handleViewCompanies = async () => {
  try {
    const response = await apiClient.getCompanies({ limit: 10 })
    companies.value = response.companies
    console.log('Loaded companies:', companies.value.length)
  } catch (error) {
    console.error('Error loading companies:', error)
  }
}

// Handle sign in
const handleSignIn = () => {
  console.log('Redirecting to sign in page...')
  showAuthPrompt.value = false
  // Future: Redirect to login page or open login modal
}

// Handle sign out
const handleSignOut = () => {
  signOut()
  console.log('Signed out')
}

// Simulate login for demo purposes
const simulateLogin = () => {
  // This is just for demonstration
  // In a real app, this would be handled by the authentication system
  const fakeToken = 'demo-token-' + Date.now()
  apiClient.setAuthToken(fakeToken)
  console.log('Simulated login with token:', fakeToken)
  window.location.reload() // Reload to update auth state
}
</script>

<style scoped>
.example-container {
  @apply max-w-4xl mx-auto p-6;
}

.example-card {
  @apply bg-white rounded-lg shadow-md p-6 border border-gray-200;
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
