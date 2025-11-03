<template>
  <div class="example-container">
    <h1 class="example-title">PDF Viewer Component Examples</h1>
    
    <!-- Example 1: Basic Usage -->
    <section class="example-section">
      <h2 class="section-title">Example 1: Basic PDF Viewer</h2>
      <p class="section-description">
        Simple PDF viewer with navigation and zoom controls.
      </p>
      <button class="example-button" @click="showBasicViewer = true">
        Open Basic PDF Viewer
      </button>
    </section>

    <!-- Example 2: With Initial Page -->
    <section class="example-section">
      <h2 class="section-title">Example 2: Open to Specific Page</h2>
      <p class="section-description">
        Open PDF viewer directly to page 5.
      </p>
      <button class="example-button" @click="showPageViewer = true">
        Open to Page 5
      </button>
    </section>

    <!-- Example 3: With Text Highlighting -->
    <section class="example-section">
      <h2 class="section-title">Example 3: With Text Highlighting</h2>
      <p class="section-description">
        Open PDF viewer with specific text highlighted on the page.
      </p>
      <div class="input-group">
        <label class="input-label">Text to highlight:</label>
        <input
          v-model="highlightText"
          type="text"
          class="text-input"
          placeholder="Enter text to highlight"
        />
      </div>
      <button class="example-button" @click="showHighlightViewer = true">
        Open with Highlighting
      </button>
    </section>

    <!-- Example 4: Citation Integration -->
    <section class="example-section">
      <h2 class="section-title">Example 4: Citation Integration</h2>
      <p class="section-description">
        Simulate clicking on a citation to view the source document.
      </p>
      <div class="citation-card">
        <div class="citation-header">
          <svg class="pdf-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
            />
          </svg>
          <div>
            <p class="citation-title">{{ mockCitation.pdfName }}</p>
            <p class="citation-pages">Pages {{ mockCitation.pages.join(', ') }}</p>
          </div>
        </div>
        <p class="citation-text">{{ mockCitation.chunkText }}</p>
        <button class="view-button" @click="handleViewCitation">
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
          View in PDF
        </button>
      </div>
    </section>

    <!-- Modal Overlays for Examples -->
    
    <!-- Basic Viewer Modal -->
    <div v-if="showBasicViewer" class="modal-overlay" @click.self="showBasicViewer = false">
      <div class="modal-container">
        <PDFViewer
          :pdf-url="samplePdfUrl"
          closeable
          @close="showBasicViewer = false"
        />
      </div>
    </div>

    <!-- Page Viewer Modal -->
    <div v-if="showPageViewer" class="modal-overlay" @click.self="showPageViewer = false">
      <div class="modal-container">
        <PDFViewer
          :pdf-url="samplePdfUrl"
          :initial-page="5"
          closeable
          @close="showPageViewer = false"
          @page-change="handlePageChange"
        />
      </div>
    </div>

    <!-- Highlight Viewer Modal -->
    <div v-if="showHighlightViewer" class="modal-overlay" @click.self="showHighlightViewer = false">
      <div class="modal-container">
        <PDFViewer
          :pdf-url="samplePdfUrl"
          :initial-page="1"
          :highlight-text="highlightText"
          closeable
          @close="showHighlightViewer = false"
        />
      </div>
    </div>

    <!-- Citation Viewer Modal -->
    <div v-if="showCitationViewer" class="modal-overlay" @click.self="showCitationViewer = false">
      <div class="modal-container">
        <PDFViewer
          :pdf-url="mockCitation.url"
          :initial-page="mockCitation.pages[0]"
          :highlight-text="mockCitation.chunkText"
          closeable
          @close="showCitationViewer = false"
        />
      </div>
    </div>

    <!-- Page Change Notification -->
    <div v-if="showPageNotification" class="notification">
      Page changed to: {{ currentPage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PDFViewer from './PDFViewer.vue'
import type { Citation } from '@/types'

// State
const showBasicViewer = ref(false)
const showPageViewer = ref(false)
const showHighlightViewer = ref(false)
const showCitationViewer = ref(false)
const showPageNotification = ref(false)
const currentPage = ref(1)
const highlightText = ref('emissions')

// Sample data
const samplePdfUrl = ref('/api/documents/RELIANCE/2024_BRSR.pdf')

const mockCitation = ref<Citation>({
  pdfName: 'RELIANCE/2024_BRSR.pdf',
  pages: [45, 46],
  chunkText: 'Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e, representing a 5% reduction from the previous year. This achievement is attributed to our ongoing investments in renewable energy and energy efficiency initiatives.',
  url: '/api/documents/RELIANCE/2024_BRSR.pdf'
})

// Methods
const handleViewCitation = () => {
  showCitationViewer.value = true
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  showPageNotification.value = true
  
  setTimeout(() => {
    showPageNotification.value = false
  }, 2000)
}
</script>

<style scoped>
.example-container {
  @apply max-w-4xl mx-auto p-6 space-y-8;
}

.example-title {
  @apply text-3xl font-bold text-gray-900 mb-8;
}

.example-section {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.section-title {
  @apply text-xl font-semibold text-gray-900 mb-2;
}

.section-description {
  @apply text-gray-600 mb-4;
}

.example-button {
  @apply px-4 py-2 bg-blue-600 text-white rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

.input-group {
  @apply mb-4;
}

.input-label {
  @apply block text-sm font-medium text-gray-700 mb-2;
}

.text-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

/* Citation Card */
.citation-card {
  @apply bg-gray-50 rounded-lg border border-gray-200 p-4 mb-4;
}

.citation-header {
  @apply flex items-start gap-3 mb-3;
}

.pdf-icon {
  @apply w-5 h-5 text-red-500 flex-shrink-0 mt-0.5;
}

.citation-title {
  @apply text-sm font-medium text-gray-900;
}

.citation-pages {
  @apply text-xs text-gray-600 mt-0.5;
}

.citation-text {
  @apply text-sm text-gray-700 mb-3 leading-relaxed;
}

.view-button {
  @apply flex items-center gap-2 px-3 py-1.5;
  @apply bg-blue-600 text-white text-sm font-medium rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

.button-icon {
  @apply w-4 h-4;
}

/* Modal */
.modal-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50 z-50;
  @apply flex items-center justify-center p-4;
}

.modal-container {
  @apply w-full max-w-6xl h-[90vh] bg-white rounded-lg overflow-hidden;
}

/* Notification */
.notification {
  @apply fixed bottom-4 right-4 px-4 py-3 bg-gray-900 text-white rounded-lg shadow-lg;
  @apply animate-fade-in-up;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fade-in-up 0.3s ease-out;
}
</style>
