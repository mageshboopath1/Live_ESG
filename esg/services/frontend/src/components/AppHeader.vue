<template>
  <header class="bg-dark-bg border-b border-dark-border sticky top-0 z-50">
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Circular Logo Icon -->
        <div class="flex items-center space-x-6">
          <router-link to="/" class="flex items-center">
            <div class="w-10 h-10 bg-gradient-to-br from-accent-green to-accent-blue rounded-full flex items-center justify-center transition-transform duration-200 hover:scale-110">
              <span class="text-dark-bg font-bold text-lg">E</span>
            </div>
          </router-link>

          <!-- Desktop Navigation - Pill-shaped buttons -->
          <div class="hidden md:flex items-center space-x-2">
            <router-link
              to="/"
              class="nav-pill"
              :class="{ 'nav-pill-active': $route.name === 'home' }"
            >
              Check Box
            </router-link>
            <router-link
              to="/comparison"
              class="nav-pill"
              :class="{ 'nav-pill-active': $route.name === 'comparison' }"
            >
              Monitoring
            </router-link>
            <a
              href="#"
              class="nav-pill"
              @click.prevent="handleSupport"
            >
              Support
            </a>
          </div>
        </div>

        <!-- Right Section: Search and User Profile -->
        <div class="flex items-center space-x-4">
          <!-- Search Icon Button -->
          <button
            @click="handleSearch"
            class="icon-btn-dark hidden sm:flex"
            aria-label="Search"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>

          <!-- User Profile Section -->
          <div class="hidden sm:flex items-center space-x-3">
            <div class="relative">
              <button
                @click="toggleUserMenu"
                class="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-accent-green rounded-full transition-all duration-200"
                aria-label="User menu"
              >
                <!-- User Avatar with notification badge -->
                <div class="relative">
                  <div class="w-9 h-9 rounded-full bg-gradient-to-br from-accent-pink to-accent-orange flex items-center justify-center text-white font-semibold text-sm">
                    U
                  </div>
                  <!-- Notification Badge -->
                  <div class="absolute -top-1 -right-1 w-4 h-4 bg-accent-orange rounded-full border-2 border-dark-bg flex items-center justify-center">
                    <span class="text-white text-xs font-bold">3</span>
                  </div>
                </div>
              </button>

              <!-- User Dropdown Menu -->
              <transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <div
                  v-if="userMenuOpen"
                  class="absolute right-0 mt-2 w-48 dropdown-dark py-2"
                >
                  <a href="#" class="block px-4 py-2 text-sm text-dark-text-primary hover:bg-dark-cardHover transition-colors" @click.prevent="handleProfile">Profile</a>
                  <a href="#" class="block px-4 py-2 text-sm text-dark-text-primary hover:bg-dark-cardHover transition-colors" @click.prevent="handleSettings">Settings</a>
                  <div class="border-t border-dark-border my-1"></div>
                  <a href="#" class="block px-4 py-2 text-sm text-dark-text-primary hover:bg-dark-cardHover transition-colors" @click.prevent="handleLogout">Logout</a>
                </div>
              </transition>
            </div>
          </div>

          <!-- Mobile Menu Button -->
          <div class="md:hidden">
            <button
              @click="toggleMobileMenu"
              class="icon-btn-dark"
              aria-label="Toggle menu"
            >
              <svg
                v-if="!mobileMenuOpen"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              <svg
                v-else
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile Menu -->
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 -translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <div v-if="mobileMenuOpen" class="md:hidden pb-4 pt-2">
          <div class="flex flex-col space-y-2">
            <router-link
              to="/"
              class="mobile-nav-pill"
              :class="{ 'mobile-nav-pill-active': $route.name === 'home' }"
              @click="closeMobileMenu"
            >
              Check Box
            </router-link>
            <router-link
              to="/comparison"
              class="mobile-nav-pill"
              :class="{ 'mobile-nav-pill-active': $route.name === 'comparison' }"
              @click="closeMobileMenu"
            >
              Monitoring
            </router-link>
            <a
              href="#"
              class="mobile-nav-pill"
              @click.prevent="handleSupport"
            >
              Support
            </a>
            <div class="border-t border-dark-border my-2"></div>
            <button
              @click="handleSearch"
              class="mobile-nav-pill text-left"
            >
              Search
            </button>
            <a href="#" class="mobile-nav-pill" @click.prevent="handleProfile">Profile</a>
            <a href="#" class="mobile-nav-pill" @click.prevent="handleSettings">Settings</a>
          </div>
        </div>
      </transition>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
  if (mobileMenuOpen.value) {
    userMenuOpen.value = false
  }
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
}

const handleSearch = () => {
  // TODO: Implement search functionality
  console.log('Search clicked')
}

const handleSupport = () => {
  // TODO: Implement support functionality
  console.log('Support clicked')
  closeMobileMenu()
}

const handleProfile = () => {
  // TODO: Implement profile navigation
  console.log('Profile clicked')
  userMenuOpen.value = false
  closeMobileMenu()
}

const handleSettings = () => {
  // TODO: Implement settings navigation
  console.log('Settings clicked')
  userMenuOpen.value = false
  closeMobileMenu()
}

const handleLogout = () => {
  // TODO: Implement logout functionality
  console.log('Logout clicked')
  userMenuOpen.value = false
  closeMobileMenu()
}

// Close mobile menu on route change
router.afterEach(() => {
  closeMobileMenu()
  userMenuOpen.value = false
})

// Close user menu when clicking outside
if (typeof window !== 'undefined') {
  window.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    if (!target.closest('[aria-label="User menu"]') && !target.closest('.dropdown-dark')) {
      userMenuOpen.value = false
    }
  })
}
</script>

<style scoped>
/* Pill-shaped navigation buttons */
.nav-pill {
  @apply px-6 py-2 text-sm font-medium text-dark-text-secondary rounded-full 
         bg-dark-card hover:bg-dark-cardHover hover:text-dark-text-primary 
         transition-all duration-200 border border-transparent;
}

.nav-pill-active {
  @apply text-dark-text-primary bg-dark-cardHover border-dark-border;
}

/* Mobile navigation pills */
.mobile-nav-pill {
  @apply block px-6 py-3 text-base font-medium text-dark-text-secondary rounded-full 
         bg-dark-card hover:bg-dark-cardHover hover:text-dark-text-primary 
         transition-all duration-200;
}

.mobile-nav-pill-active {
  @apply text-dark-text-primary bg-dark-cardHover;
}

/* Smooth hover effects for interactive elements */
.nav-pill:hover,
.mobile-nav-pill:hover,
.icon-btn-dark:hover {
  transform: translateY(-1px);
}

/* Focus states for accessibility */
.nav-pill:focus,
.mobile-nav-pill:focus {
  @apply outline-none ring-2 ring-accent-green ring-offset-2 ring-offset-dark-bg;
}
</style>
