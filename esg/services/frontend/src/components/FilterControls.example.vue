<template>
  <div class="example-container">
    <h1 class="example-title">FilterControls Component Example</h1>
    
    <div class="example-section">
      <h2 class="section-title">Basic Usage</h2>
      <FilterControls
        v-model:selected-date="filters.date"
        v-model:selected-product="filters.product"
        v-model:selected-profile="filters.profile"
        @export="handleExport"
      />
    </div>

    <div class="example-section">
      <h2 class="section-title">Current Filter Values</h2>
      <div class="filter-values">
        <div class="value-item">
          <span class="value-label">Date:</span>
          <span class="value-text">{{ filters.date }}</span>
        </div>
        <div class="value-item">
          <span class="value-label">Product:</span>
          <span class="value-text">{{ filters.product }}</span>
        </div>
        <div class="value-item">
          <span class="value-label">Profile:</span>
          <span class="value-text">{{ filters.profile }}</span>
        </div>
      </div>
    </div>

    <div class="example-section">
      <h2 class="section-title">Custom Options</h2>
      <FilterControls
        v-model:selected-date="customFilters.date"
        v-model:selected-product="customFilters.product"
        v-model:selected-profile="customFilters.profile"
        :date-options="customDateOptions"
        :product-options="customProductOptions"
        :profile-options="customProfileOptions"
        @export="handleExport"
      />
    </div>

    <div class="example-section">
      <h2 class="section-title">Export Events</h2>
      <div class="event-log">
        <p v-if="exportCount === 0" class="text-dark-text-muted">
          Click the export button to see events
        </p>
        <p v-else class="text-accent-green">
          Export clicked {{ exportCount }} time{{ exportCount > 1 ? 's' : '' }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import FilterControls from './FilterControls.vue'

// Basic filters
const filters = reactive({
  date: '30d',
  product: 'all',
  profile: 'all'
})

// Custom filters
const customFilters = reactive({
  date: 'q1',
  product: 'custom1',
  profile: 'custom1'
})

// Custom options
const customDateOptions = [
  { label: 'Q1 2024', value: 'q1' },
  { label: 'Q2 2024', value: 'q2' },
  { label: 'Q3 2024', value: 'q3' },
  { label: 'Q4 2024', value: 'q4' }
]

const customProductOptions = [
  { label: 'Custom Product 1', value: 'custom1' },
  { label: 'Custom Product 2', value: 'custom2' },
  { label: 'Custom Product 3', value: 'custom3' }
]

const customProfileOptions = [
  { label: 'Custom Profile A', value: 'custom1' },
  { label: 'Custom Profile B', value: 'custom2' },
  { label: 'Custom Profile C', value: 'custom3' }
]

// Export tracking
const exportCount = ref(0)

const handleExport = () => {
  exportCount.value++
  console.log('Export triggered with filters:', filters)
}
</script>

<style scoped>
.example-container {
  @apply min-h-screen bg-dark-bg p-8;
}

.example-title {
  @apply text-4xl font-bold text-dark-text-primary mb-8;
}

.example-section {
  @apply mb-12;
}

.section-title {
  @apply text-2xl font-semibold text-dark-text-primary mb-4;
}

.filter-values {
  @apply bg-dark-card rounded-lg p-6 border border-dark-border space-y-3;
}

.value-item {
  @apply flex items-center gap-3;
}

.value-label {
  @apply text-sm font-medium text-dark-text-secondary min-w-[100px];
}

.value-text {
  @apply text-sm text-accent-green font-mono;
}

.event-log {
  @apply bg-dark-card rounded-lg p-6 border border-dark-border;
}
</style>
