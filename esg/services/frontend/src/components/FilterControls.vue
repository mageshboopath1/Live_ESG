<template>
  <div class="filter-controls">
    <!-- Filter Buttons -->
    <div class="filter-buttons">
      <!-- Date Filter -->
      <div class="filter-dropdown" ref="dateDropdownRef">
        <button
          class="filter-button"
          @click="toggleDropdown('date')"
          :aria-expanded="activeDropdown === 'date'"
          aria-haspopup="true"
        >
          <span class="filter-label">Date</span>
          <span class="filter-value">{{ selectedDateLabel }}</span>
          <svg
            class="chevron-icon"
            :class="{ 'rotate-180': activeDropdown === 'date' }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <!-- Date Dropdown Menu -->
        <transition name="dropdown">
          <div v-if="activeDropdown === 'date'" class="dropdown-menu">
            <button
              v-for="option in dateOptions"
              :key="option.value"
              class="dropdown-item"
              :class="{ active: selectedDate === option.value }"
              @click="selectDate(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </transition>
      </div>

      <!-- Product Filter -->
      <div class="filter-dropdown" ref="productDropdownRef">
        <button
          class="filter-button"
          @click="toggleDropdown('product')"
          :aria-expanded="activeDropdown === 'product'"
          aria-haspopup="true"
        >
          <span class="filter-label">Product</span>
          <span class="filter-value">{{ selectedProductLabel }}</span>
          <svg
            class="chevron-icon"
            :class="{ 'rotate-180': activeDropdown === 'product' }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <!-- Product Dropdown Menu -->
        <transition name="dropdown">
          <div v-if="activeDropdown === 'product'" class="dropdown-menu">
            <button
              v-for="option in productOptions"
              :key="option.value"
              class="dropdown-item"
              :class="{ active: selectedProduct === option.value }"
              @click="selectProduct(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </transition>
      </div>

      <!-- Profile Filter -->
      <div class="filter-dropdown" ref="profileDropdownRef">
        <button
          class="filter-button"
          @click="toggleDropdown('profile')"
          :aria-expanded="activeDropdown === 'profile'"
          aria-haspopup="true"
        >
          <span class="filter-label">Profile</span>
          <span class="filter-value">{{ selectedProfileLabel }}</span>
          <svg
            class="chevron-icon"
            :class="{ 'rotate-180': activeDropdown === 'profile' }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <!-- Profile Dropdown Menu -->
        <transition name="dropdown">
          <div v-if="activeDropdown === 'profile'" class="dropdown-menu">
            <button
              v-for="option in profileOptions"
              :key="option.value"
              class="dropdown-item"
              :class="{ active: selectedProfile === option.value }"
              @click="selectProfile(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </transition>
      </div>
    </div>

    <!-- Export Button -->
    <button
      class="export-button"
      @click="handleExport"
      aria-label="Print or export data"
      title="Print or export"
    >
      <svg
        class="export-icon"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Types
interface FilterOption {
  label: string
  value: string
}

// Props
interface Props {
  dateOptions?: FilterOption[]
  productOptions?: FilterOption[]
  profileOptions?: FilterOption[]
  selectedDate?: string
  selectedProduct?: string
  selectedProfile?: string
}

const props = withDefaults(defineProps<Props>(), {
  dateOptions: () => [
    { label: 'Last 7 days', value: '7d' },
    { label: 'Last 30 days', value: '30d' },
    { label: 'Last 90 days', value: '90d' },
    { label: 'Last year', value: '1y' },
    { label: 'All time', value: 'all' }
  ],
  productOptions: () => [
    { label: 'All Products', value: 'all' },
    { label: 'ESG Scores', value: 'esg' },
    { label: 'Reports', value: 'reports' },
    { label: 'Analytics', value: 'analytics' }
  ],
  profileOptions: () => [
    { label: 'All Profiles', value: 'all' },
    { label: 'Environmental', value: 'environmental' },
    { label: 'Social', value: 'social' },
    { label: 'Governance', value: 'governance' }
  ],
  selectedDate: '30d',
  selectedProduct: 'all',
  selectedProfile: 'all'
})

// Emits
const emit = defineEmits<{
  'update:selectedDate': [value: string]
  'update:selectedProduct': [value: string]
  'update:selectedProfile': [value: string]
  'export': []
}>()

// State
const activeDropdown = ref<'date' | 'product' | 'profile' | null>(null)
const dateDropdownRef = ref<HTMLElement | null>(null)
const productDropdownRef = ref<HTMLElement | null>(null)
const profileDropdownRef = ref<HTMLElement | null>(null)

// Computed labels
const selectedDateLabel = computed(() => {
  const option = props.dateOptions.find(opt => opt.value === props.selectedDate)
  return option?.label || 'Select date'
})

const selectedProductLabel = computed(() => {
  const option = props.productOptions.find(opt => opt.value === props.selectedProduct)
  return option?.label || 'Select product'
})

const selectedProfileLabel = computed(() => {
  const option = props.profileOptions.find(opt => opt.value === props.selectedProfile)
  return option?.label || 'Select profile'
})

// Methods
const toggleDropdown = (dropdown: 'date' | 'product' | 'profile') => {
  if (activeDropdown.value === dropdown) {
    activeDropdown.value = null
  } else {
    activeDropdown.value = dropdown
  }
}

const selectDate = (value: string) => {
  emit('update:selectedDate', value)
  activeDropdown.value = null
}

const selectProduct = (value: string) => {
  emit('update:selectedProduct', value)
  activeDropdown.value = null
}

const selectProfile = (value: string) => {
  emit('update:selectedProfile', value)
  activeDropdown.value = null
}

const handleExport = () => {
  emit('export')
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  
  if (
    activeDropdown.value &&
    !dateDropdownRef.value?.contains(target) &&
    !productDropdownRef.value?.contains(target) &&
    !profileDropdownRef.value?.contains(target)
  ) {
    activeDropdown.value = null
  }
}

// Close dropdown on escape key
const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && activeDropdown.value) {
    activeDropdown.value = null
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.filter-controls {
  @apply flex items-center gap-4 flex-wrap;
}

.filter-buttons {
  @apply flex items-center gap-3 flex-1 flex-wrap;
}

.filter-dropdown {
  @apply relative;
}

.filter-button {
  @apply flex items-center gap-3 px-6 py-2.5 bg-dark-card text-dark-text-primary rounded-full;
  @apply hover:bg-dark-cardHover transition-all duration-200 border border-dark-border;
  @apply focus:outline-none focus:ring-2 focus:ring-accent-green focus:ring-offset-2 focus:ring-offset-dark-bg;
}

.filter-label {
  @apply text-sm text-dark-text-secondary;
}

.filter-value {
  @apply text-sm font-medium text-dark-text-primary;
}

.chevron-icon {
  @apply w-4 h-4 text-dark-text-secondary transition-transform duration-200;
}

.dropdown-menu {
  @apply absolute top-full left-0 mt-2 min-w-[200px] bg-dark-card border border-dark-border rounded-lg;
  @apply shadow-dark-lg z-50 py-2;
}

.dropdown-item {
  @apply w-full px-4 py-2.5 text-left text-sm text-dark-text-primary;
  @apply hover:bg-dark-cardHover transition-colors duration-150;
  @apply focus:outline-none focus:bg-dark-cardHover;
}

.dropdown-item.active {
  @apply bg-dark-cardHover text-accent-green font-medium;
}

.export-button {
  @apply p-2.5 rounded-full bg-dark-card text-dark-text-secondary;
  @apply hover:bg-dark-cardHover hover:text-dark-text-primary transition-all duration-200;
  @apply border border-dark-border;
  @apply focus:outline-none focus:ring-2 focus:ring-accent-green focus:ring-offset-2 focus:ring-offset-dark-bg;
}

.export-icon {
  @apply w-5 h-5;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  @apply transition-all duration-200;
}

.dropdown-enter-from,
.dropdown-leave-to {
  @apply opacity-0 transform scale-95 -translate-y-2;
}

.dropdown-enter-to,
.dropdown-leave-from {
  @apply opacity-100 transform scale-100 translate-y-0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .filter-controls {
    @apply flex-col items-stretch gap-3;
  }

  .filter-buttons {
    @apply flex-col gap-2;
  }

  .filter-button {
    @apply w-full justify-between;
  }

  .export-button {
    @apply w-full justify-center;
  }

  .dropdown-menu {
    @apply left-0 right-0 w-full;
  }
}
</style>
