<template>
  <div class="indicator-card">
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-content">
        <h3 class="indicator-name">{{ indicator.name }}</h3>
        <span class="indicator-code">{{ indicator.code }}</span>
      </div>
      <div class="pillar-badge" :class="`pillar-${indicator.pillar.toLowerCase()}`">
        {{ indicator.pillar }}
      </div>
    </div>

    <!-- Card Body -->
    <div class="card-body">
      <!-- Value Display -->
      <div class="value-container">
        <span class="value-text">{{ indicator.value }}</span>
        <span v-if="indicator.unit" class="unit-text">{{ indicator.unit }}</span>
      </div>

      <!-- Metadata Row -->
      <div class="metadata-row">
        <!-- Confidence Badge -->
        <div class="confidence-badge" :class="confidenceClass">
          <svg class="badge-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span class="badge-text">{{ confidencePercentage }}% confidence</span>
        </div>

        <!-- Validation Status Badge -->
        <div class="validation-badge" :class="validationClass">
          <svg
            v-if="indicator.validationStatus === 'valid'"
            class="badge-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          <svg
            v-else-if="indicator.validationStatus === 'invalid'"
            class="badge-icon"
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
          <svg
            v-else
            class="badge-icon"
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
          <span class="badge-text">{{ validationStatusText }}</span>
        </div>
      </div>
    </div>

    <!-- Card Footer - Citation -->
    <div v-if="showCitation" class="card-footer">
      <button
        class="citation-button"
        @click="handleCitationClick"
        @keypress.enter="handleCitationClick"
        aria-label="View source citation"
      >
        <svg class="citation-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <div class="citation-content">
          <span class="citation-label">Source:</span>
          <span class="citation-text">{{ citationText }}</span>
        </div>
        <svg class="citation-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Indicator } from '@/types'

// Props
interface Props {
  indicator: Indicator
  pdfName?: string
  sourcePages?: number[]
  showCitation?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  pdfName: '',
  sourcePages: () => [],
  showCitation: true
})

// Emits
const emit = defineEmits<{
  (e: 'citationClick', indicator: Indicator): void
}>()

// Computed
const confidencePercentage = computed(() => {
  return Math.round(props.indicator.confidence * 100)
})

const confidenceClass = computed(() => {
  const confidence = props.indicator.confidence
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.6) return 'confidence-medium'
  return 'confidence-low'
})

const validationClass = computed(() => {
  const status = props.indicator.validationStatus
  return `validation-${status}`
})

const validationStatusText = computed(() => {
  const status = props.indicator.validationStatus
  return status.charAt(0).toUpperCase() + status.slice(1)
})

const citationText = computed(() => {
  if (!props.pdfName && props.sourcePages.length === 0) {
    return 'View citation'
  }

  const fileName = props.pdfName.split('/').pop() || props.pdfName
  const pages = props.sourcePages.length > 0 
    ? `Page${props.sourcePages.length > 1 ? 's' : ''} ${formatPages(props.sourcePages)}`
    : ''

  if (fileName && pages) {
    return `${fileName} - ${pages}`
  } else if (fileName) {
    return fileName
  } else if (pages) {
    return pages
  }
  
  return 'View citation'
})

// Methods
const formatPages = (pages: number[]): string => {
  if (pages.length === 0) return ''
  if (pages.length === 1) return pages[0].toString()
  if (pages.length === 2) return pages.join(', ')
  
  // For more than 2 pages, show first and last with ellipsis
  const sorted = [...pages].sort((a, b) => a - b)
  return `${sorted[0]}, ..., ${sorted[sorted.length - 1]}`
}

const handleCitationClick = () => {
  emit('citationClick', props.indicator)
}
</script>

<style scoped>
.indicator-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200;
  @apply hover:shadow-md transition-shadow duration-200;
  @apply overflow-hidden;
}

/* Header */
.card-header {
  @apply flex items-start justify-between gap-3 p-4 pb-3 border-b border-gray-100;
}

.header-content {
  @apply flex-1 min-w-0;
}

.indicator-name {
  @apply text-base font-semibold text-gray-900 mb-1;
  @apply line-clamp-2;
}

.indicator-code {
  @apply inline-block px-2 py-0.5 text-xs font-mono bg-gray-100 text-gray-600 rounded;
}

.pillar-badge {
  @apply flex-shrink-0 w-8 h-8 rounded-full;
  @apply flex items-center justify-center;
  @apply text-sm font-bold text-white;
}

.pillar-e {
  @apply bg-green-500;
}

.pillar-s {
  @apply bg-blue-500;
}

.pillar-g {
  @apply bg-purple-500;
}

/* Body */
.card-body {
  @apply p-4 space-y-3;
}

.value-container {
  @apply flex items-baseline gap-2;
}

.value-text {
  @apply text-2xl font-bold text-gray-900;
}

.unit-text {
  @apply text-sm text-gray-600;
}

.metadata-row {
  @apply flex flex-wrap items-center gap-2;
}

/* Badges */
.confidence-badge,
.validation-badge {
  @apply flex items-center gap-1.5 px-2.5 py-1 rounded-full;
  @apply text-xs font-medium;
}

.badge-icon {
  @apply w-4 h-4;
}

.badge-text {
  @apply leading-none;
}

/* Confidence Badges */
.confidence-high {
  @apply bg-green-100 text-green-800;
}

.confidence-medium {
  @apply bg-yellow-100 text-yellow-800;
}

.confidence-low {
  @apply bg-orange-100 text-orange-800;
}

/* Validation Badges */
.validation-valid {
  @apply bg-green-100 text-green-800;
}

.validation-invalid {
  @apply bg-red-100 text-red-800;
}

.validation-pending {
  @apply bg-gray-100 text-gray-800;
}

/* Footer - Citation */
.card-footer {
  @apply border-t border-gray-100;
}

.citation-button {
  @apply w-full flex items-center gap-3 p-3;
  @apply text-left hover:bg-gray-50 transition-colors duration-150;
  @apply focus:outline-none focus:bg-gray-50;
  @apply cursor-pointer;
}

.citation-icon {
  @apply w-5 h-5 text-gray-400 flex-shrink-0;
}

.citation-content {
  @apply flex-1 min-w-0 flex flex-col gap-0.5;
}

.citation-label {
  @apply text-xs text-gray-500 font-medium;
}

.citation-text {
  @apply text-sm text-gray-700 truncate;
}

.citation-arrow {
  @apply w-4 h-4 text-gray-400 flex-shrink-0;
}

.citation-button:hover .citation-arrow {
  @apply text-blue-600 transform translate-x-0.5 transition-transform;
}

.citation-button:hover .citation-text {
  @apply text-blue-600;
}
</style>
