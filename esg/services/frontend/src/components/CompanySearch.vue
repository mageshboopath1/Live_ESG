<template>
  <div class="company-search">
    <!-- Search Input -->
    <div class="search-container">
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search companies by name or symbol..."
          class="search-input"
          @focus="showResults = true"
        />
        <svg
          class="search-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="clear-button"
          aria-label="Clear search"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
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

      <!-- Industry Filter -->
      <div class="filter-container">
        <label for="industry-filter" class="filter-label">Industry:</label>
        <select
          id="industry-filter"
          v-model="selectedIndustry"
          class="filter-select"
        >
          <option value="">All Industries</option>
          <option
            v-for="industry in industries"
            :key="industry"
            :value="industry"
          >
            {{ industry }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="text-gray-600">Searching companies...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-container">
      <svg
        class="error-icon"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Search Results -->
    <div
      v-if="showResults && (searchQuery || selectedIndustry) && !loading"
      class="results-container"
    >
      <div v-if="filteredCompanies.length === 0" class="no-results">
        <p class="text-gray-600">No companies found</p>
      </div>

      <div v-else class="results-grid">
        <div
          v-for="company in filteredCompanies"
          :key="company.id"
          class="company-card"
          @click="selectCompany(company)"
          @keypress.enter="selectCompany(company)"
          tabindex="0"
          role="button"
        >
          <div class="company-card-header">
            <h3 class="company-name">{{ company.company_name }}</h3>
            <span class="company-symbol">{{ company.symbol }}</span>
          </div>
          <div class="company-card-body">
            <p class="company-industry">
              <svg
                class="industry-icon"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
              {{ company.industry || 'N/A' }}
            </p>
            <p class="company-isin">ISIN: {{ company.isin_code }}</p>
          </div>
          <div class="company-card-footer">
            <span class="view-details">View Details →</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import type { Company } from '@/types'

// Props
interface Props {
  autoFocus?: boolean
  showIndustryFilter?: boolean
}

withDefaults(defineProps<Props>(), {
  autoFocus: false,
  showIndustryFilter: true
})

// Emits
const emit = defineEmits<{
  (e: 'select', company: Company): void
}>()

// Router
const router = useRouter()

// Store
const companyStore = useCompanyStore()

// State
const searchQuery = ref('')
const selectedIndustry = ref('')
const showResults = ref(false)
const searchResults = ref<Company[]>([])
const allCompanies = ref<Company[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// Computed
const industries = computed(() => {
  const uniqueIndustries = new Set(
    allCompanies.value
      .map((c) => c.industry)
      .filter((i) => i && i.trim() !== '')
  )
  return Array.from(uniqueIndustries).sort()
})

const filteredCompanies = computed(() => {
  let results = searchQuery.value ? searchResults.value : allCompanies.value

  // Apply industry filter
  if (selectedIndustry.value) {
    results = results.filter((c) => c.industry === selectedIndustry.value)
  }

  return results
})

// Methods
const performSearch = async (query: string) => {
  if (!query.trim()) {
    searchResults.value = []
    return
  }

  loading.value = true
  error.value = null

  try {
    const results = await companyStore.searchCompanies(query)
    searchResults.value = results
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Search failed'
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

const debouncedSearch = (query: string) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(() => {
    performSearch(query)
  }, 300) // 300ms debounce delay
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  error.value = null
}

const selectCompany = (company: Company) => {
  emit('select', company)
  companyStore.selectCompany(company)
  router.push({ name: 'company', params: { id: company.id } })
  showResults.value = false
}

const loadAllCompanies = async () => {
  loading.value = true
  error.value = null

  try {
    await companyStore.fetchCompanies()
    allCompanies.value = companyStore.companies
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load companies'
  } finally {
    loading.value = false
  }
}

// Watchers
watch(searchQuery, (newQuery) => {
  if (newQuery.trim()) {
    debouncedSearch(newQuery)
  } else {
    searchResults.value = []
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
  }
})

watch(selectedIndustry, () => {
  showResults.value = true
})

// Lifecycle
onMounted(() => {
  loadAllCompanies()
})

// Click outside to close results
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.company-search')) {
    showResults.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
})
</script>

<style scoped>
.company-search {
  @apply w-full;
}

.search-container {
  @apply space-y-4;
}

.search-input {
  @apply w-full px-4 py-3 pl-12 pr-12 text-lg border border-gray-300 rounded-lg;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  @apply transition-all duration-200;
}

.search-icon {
  @apply absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400;
}

.clear-button {
  @apply absolute right-4 top-1/2 transform -translate-y-1/2;
  @apply text-gray-400 hover:text-gray-600 transition-colors;
}

.filter-container {
  @apply flex items-center gap-3;
}

.filter-label {
  @apply text-sm font-medium text-gray-700;
}

.filter-select {
  @apply flex-1 px-4 py-2 border border-gray-300 rounded-lg;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  @apply transition-all duration-200;
}

.loading-container {
  @apply flex items-center justify-center gap-3 py-8;
}

.spinner {
  @apply w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin;
}

.error-container {
  @apply flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg;
}

.error-icon {
  @apply w-5 h-5 text-red-500;
}

.results-container {
  @apply mt-4;
}

.no-results {
  @apply text-center py-8;
}

.results-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.company-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-4;
  @apply hover:shadow-md hover:border-blue-300 transition-all duration-200;
  @apply cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.company-card-header {
  @apply flex items-start justify-between gap-2 mb-3;
}

.company-name {
  @apply text-lg font-semibold text-gray-900 line-clamp-2;
}

.company-symbol {
  @apply px-2 py-1 text-xs font-mono font-bold bg-blue-100 text-blue-700 rounded;
  @apply flex-shrink-0;
}

.company-card-body {
  @apply space-y-2 mb-3;
}

.company-industry {
  @apply flex items-center gap-2 text-sm text-gray-600;
}

.industry-icon {
  @apply w-4 h-4;
}

.company-isin {
  @apply text-xs text-gray-500 font-mono;
}

.company-card-footer {
  @apply pt-3 border-t border-gray-100;
}

.view-details {
  @apply text-sm text-blue-600 font-medium;
}

.company-card:hover .view-details {
  @apply text-blue-700;
}
</style>
