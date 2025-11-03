<template>
  <aside
    :class="[
      'fixed left-0 top-0 h-screen bg-dark-bg border-r border-dark-border transition-all duration-300 z-40',
      'flex flex-col items-center py-6',
      isOpen ? 'w-20' : 'w-0 -translate-x-full md:translate-x-0 md:w-20'
    ]"
  >
    <!-- Top spacing for header -->
    <div class="h-16"></div>

    <!-- Navigation Icons -->
    <nav class="flex-1 flex flex-col items-center gap-6 mt-4">
      <!-- Favorites -->
      <button
        @click="handleAction('favorite')"
        :class="[
          'icon-btn-dark relative group',
          activeSection === 'favorite' && 'text-accent-pink'
        ]"
        :aria-label="'Favorites'"
        :title="'Favorites'"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
          />
        </svg>
        <!-- Tooltip -->
        <span
          class="absolute left-full ml-4 px-3 py-1.5 bg-dark-card border border-dark-border rounded-lg text-sm text-dark-text-primary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
        >
          Favorites
        </span>
      </button>

      <!-- Calendar -->
      <button
        @click="handleAction('calendar')"
        :class="[
          'icon-btn-dark relative group',
          activeSection === 'calendar' && 'text-accent-blue'
        ]"
        :aria-label="'Calendar'"
        :title="'Calendar'"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <!-- Tooltip -->
        <span
          class="absolute left-full ml-4 px-3 py-1.5 bg-dark-card border border-dark-border rounded-lg text-sm text-dark-text-primary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
        >
          Calendar
        </span>
      </button>

      <!-- Insights (Diamond) -->
      <button
        @click="handleAction('insights')"
        :class="[
          'icon-btn-dark relative group',
          activeSection === 'insights' && 'text-accent-green'
        ]"
        :aria-label="'Insights'"
        :title="'Insights'"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <!-- Tooltip -->
        <span
          class="absolute left-full ml-4 px-3 py-1.5 bg-dark-card border border-dark-border rounded-lg text-sm text-dark-text-primary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
        >
          Insights
        </span>
      </button>

      <!-- Settings -->
      <button
        @click="handleAction('settings')"
        :class="[
          'icon-btn-dark relative group',
          activeSection === 'settings' && 'text-accent-orange'
        ]"
        :aria-label="'Settings'"
        :title="'Settings'"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <!-- Tooltip -->
        <span
          class="absolute left-full ml-4 px-3 py-1.5 bg-dark-card border border-dark-border rounded-lg text-sm text-dark-text-primary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
        >
          Settings
        </span>
      </button>
    </nav>

    <!-- Add/Create Button at Bottom -->
    <button
      @click="handleAction('add')"
      class="icon-btn-dark relative group bg-accent-green hover:bg-accent-green-dark text-dark-bg mb-4"
      :aria-label="'Add new'"
      :title="'Add new'"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 4v16m8-8H4"
        />
      </svg>
      <!-- Tooltip -->
      <span
        class="absolute left-full ml-4 px-3 py-1.5 bg-dark-card border border-dark-border rounded-lg text-sm text-dark-text-primary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
      >
        Add new
      </span>
    </button>
  </aside>

  <!-- Mobile Toggle Button -->
  <button
    v-if="!isOpen"
    @click="toggleSidebar"
    class="fixed left-4 top-20 z-50 md:hidden p-2 bg-dark-card border border-dark-border rounded-lg text-dark-text-primary hover:bg-dark-cardHover transition-all duration-200"
    :aria-label="'Open sidebar'"
  >
    <svg
      class="w-6 h-6"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  </button>

  <!-- Mobile Overlay -->
  <Transition name="fade">
    <div
      v-if="isOpen && isMobile"
      @click="toggleSidebar"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
    ></div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUIStore } from '@/stores/uiStore'

type ActionType = 'favorite' | 'calendar' | 'insights' | 'settings' | 'add'

// Props
interface Props {
  activeSection?: ActionType
}

withDefaults(defineProps<Props>(), {
  activeSection: undefined
})

// Emits
const emit = defineEmits<{
  action: [actionType: ActionType]
  toggle: []
}>()

// Store
const uiStore = useUIStore()

// State
const isMobile = ref(false)

// Computed
const isOpen = computed(() => uiStore.sidebarOpen)

// Methods
const handleAction = (actionType: ActionType) => {
  emit('action', actionType)
}

const toggleSidebar = () => {
  uiStore.toggleSidebar()
  emit('toggle')
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  
  // Auto-close sidebar on mobile
  if (isMobile.value && isOpen.value) {
    uiStore.setSidebarOpen(false)
  } else if (!isMobile.value && !isOpen.value) {
    uiStore.setSidebarOpen(true)
  }
}

// Lifecycle
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
/* Fade transition for mobile overlay */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
