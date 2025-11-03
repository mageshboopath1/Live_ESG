<template>
  <div class="citation-viewer">
    <!-- Header -->
    <div class="viewer-header">
      <h3 class="viewer-title">Source Citations</h3>
      <button
        v-if="closeable"
        class="close-button"
        @click="handleClose"
        aria-label="Close citation viewer"
      >
        <svg class="close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="loading-text">Loading citations...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="error-text">{{ error }}</p>
      <button class="retry-button" @click="handleRetry">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="citations.length === 0" class="empty-container">
      <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <p class="empty-text">No citations available</p>
    </div>

    <!-- Citations List -->
    <div v-else class="citations-list">
      <div
        v-for="(citation, index) in citations"
        :key="index"
        class="citation-card"
      >
        <!-- Citation Header -->
        <div class="citation-header">
          <div class="citation-info">
            <svg class="pdf-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <div class="citation-details">
              <p class="pdf-name">{{ formatPdfName(citation.pdfName) }}</p>
              <p class="page-numbers">{{ formatPages(citation.pages) }}</p>
            </div>
          </div>
          <span v-if="showConfidence && confidence" class="confidence-badge" :class="confidenceClass">
            {{ confidencePercentage }}%
          </span>
        </div>

        <!-- Citation Content -->
        <div class="citation-content">
          <p class="chunk-text">{{ citation.chunkText }}</p>
        </div>

        <!-- Citation Footer -->
        <div class="citation-footer">
          <div v-if="showTimestamp && extractedAt" class="timestamp">
            <svg class="timestamp-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span class="timestamp-text">Extracted {{ formatTimestamp(extractedAt) }}</span>
          </div>
          <button
            class="view-pdf-button"
            @click="handleViewPdf(citation)"
            aria-label="View in PDF"
          >
            <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
            <span>View in PDF</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Citation } from '@/types'

// Props
interface Props {
  citations: Citation[]
  loading?: boolean
  error?: string | null
  confidence?: number
  extractedAt?: string
  showConfidence?: boolean
  showTimestamp?: boolean
  closeable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
  confidence: undefined,
  extractedAt: undefined,
  showConfidence: true,
  showTimestamp: true,
  closeable: false
})

// Emits
const emit = defineEmits<{
  (e: 'viewPdf', citation: Citation): void
  (e: 'close'): void
  (e: 'retry'): void
}>()

// Computed
const confidencePercentage = computed(() => {
  if (props.confidence === undefined) return 0
  return Math.round(props.confidence * 100)
})

const confidenceClass = computed(() => {
  if (props.confidence === undefined) return ''
  const confidence = props.confidence
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.6) return 'confidence-medium'
  return 'confidence-low'
})

// Methods
const formatPdfName = (pdfName: string): string => {
  // Extract filename from path
  const parts = pdfName.split('/')
  return parts[parts.length - 1] || pdfName
}

const formatPages = (pages: number[]): string => {
  if (pages.length === 0) return 'No pages'
  if (pages.length === 1) return `Page ${pages[0]}`
  if (pages.length === 2) return `Pages ${pages[0]}, ${pages[1]}`
  
  // For more than 2 pages, show range or list
  const sorted = [...pages].sort((a, b) => a - b)
  const isConsecutive = sorted.every((page, i) => i === 0 || page === sorted[i - 1] + 1)
  
  if (isConsecutive) {
    return `Pages ${sorted[0]}-${sorted[sorted.length - 1]}`
  }
  
  if (pages.length <= 5) {
    return `Pages ${sorted.join(', ')}`
  }
  
  return `Pages ${sorted[0]}, ${sorted[1]}, ..., ${sorted[sorted.length - 1]} (${pages.length} total)`
}

const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch {
    return timestamp
  }
}

const handleViewPdf = (citation: Citation) => {
  emit('viewPdf', citation)
}

const handleClose = () => {
  emit('close')
}

const handleRetry = () => {
  emit('retry')
}
</script>

<style scoped>
.citation-viewer {
  @apply bg-white rounded-lg shadow-sm border border-gray-200;
  @apply overflow-hidden;
}

/* Header */
.viewer-header {
  @apply flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50;
}

.viewer-title {
  @apply text-lg font-semibold text-gray-900;
}

.close-button {
  @apply p-1 rounded-md hover:bg-gray-200 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.close-icon {
  @apply w-5 h-5 text-gray-600;
}

/* Loading State */
.loading-container {
  @apply flex flex-col items-center justify-center py-12 px-4;
}

.spinner {
  @apply w-10 h-10 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin;
}

.loading-text {
  @apply mt-4 text-sm text-gray-600;
}

/* Error State */
.error-container {
  @apply flex flex-col items-center justify-center py-12 px-4;
}

.error-icon {
  @apply w-12 h-12 text-red-500;
}

.error-text {
  @apply mt-4 text-sm text-gray-700 text-center;
}

.retry-button {
  @apply mt-4 px-4 py-2 bg-blue-600 text-white rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

/* Empty State */
.empty-container {
  @apply flex flex-col items-center justify-center py-12 px-4;
}

.empty-icon {
  @apply w-12 h-12 text-gray-400;
}

.empty-text {
  @apply mt-4 text-sm text-gray-600;
}

/* Citations List */
.citations-list {
  @apply divide-y divide-gray-200;
}

.citation-card {
  @apply p-4 hover:bg-gray-50 transition-colors;
}

/* Citation Header */
.citation-header {
  @apply flex items-start justify-between gap-3 mb-3;
}

.citation-info {
  @apply flex items-start gap-3 flex-1 min-w-0;
}

.pdf-icon {
  @apply w-5 h-5 text-red-500 flex-shrink-0 mt-0.5;
}

.citation-details {
  @apply flex-1 min-w-0;
}

.pdf-name {
  @apply text-sm font-medium text-gray-900 truncate;
}

.page-numbers {
  @apply text-xs text-gray-600 mt-0.5;
}

.confidence-badge {
  @apply flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold;
}

.confidence-high {
  @apply bg-green-100 text-green-800;
}

.confidence-medium {
  @apply bg-yellow-100 text-yellow-800;
}

.confidence-low {
  @apply bg-orange-100 text-orange-800;
}

/* Citation Content */
.citation-content {
  @apply mb-3;
}

.chunk-text {
  @apply text-sm text-gray-700 leading-relaxed;
  @apply bg-gray-50 rounded-md p-3 border border-gray-200;
  @apply max-h-32 overflow-y-auto;
}

/* Citation Footer */
.citation-footer {
  @apply flex items-center justify-between gap-3;
}

.timestamp {
  @apply flex items-center gap-1.5 text-xs text-gray-500;
}

.timestamp-icon {
  @apply w-4 h-4;
}

.timestamp-text {
  @apply leading-none;
}

.view-pdf-button {
  @apply flex items-center gap-2 px-3 py-1.5;
  @apply bg-blue-600 text-white text-sm font-medium rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

.button-icon {
  @apply w-4 h-4;
}

/* Scrollbar styling for chunk text */
.chunk-text::-webkit-scrollbar {
  @apply w-2;
}

.chunk-text::-webkit-scrollbar-track {
  @apply bg-gray-100 rounded;
}

.chunk-text::-webkit-scrollbar-thumb {
  @apply bg-gray-300 rounded;
}

.chunk-text::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400;
}
</style>
