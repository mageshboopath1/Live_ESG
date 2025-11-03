<template>
  <div class="example-container">
    <h1 class="example-title">Citation Viewer Component Examples</h1>

    <!-- Example 1: Basic Usage with Multiple Citations -->
    <section class="example-section">
      <h2 class="section-title">Example 1: Multiple Citations</h2>
      <CitationViewer
        :citations="multipleCitations"
        :confidence="0.92"
        :extracted-at="extractedTimestamp"
      />
    </section>

    <!-- Example 2: Single Citation -->
    <section class="example-section">
      <h2 class="section-title">Example 2: Single Citation</h2>
      <CitationViewer
        :citations="singleCitation"
        :confidence="0.78"
        :extracted-at="extractedTimestamp"
        @view-pdf="handleViewPdf"
      />
    </section>

    <!-- Example 3: Loading State -->
    <section class="example-section">
      <h2 class="section-title">Example 3: Loading State</h2>
      <CitationViewer :citations="[]" :loading="true" />
    </section>

    <!-- Example 4: Error State -->
    <section class="example-section">
      <h2 class="section-title">Example 4: Error State</h2>
      <CitationViewer
        :citations="[]"
        error="Failed to load citations. Please try again."
        @retry="handleRetry"
      />
    </section>

    <!-- Example 5: Empty State -->
    <section class="example-section">
      <h2 class="section-title">Example 5: Empty State</h2>
      <CitationViewer :citations="[]" />
    </section>

    <!-- Example 6: With Close Button -->
    <section class="example-section">
      <h2 class="section-title">Example 6: Closeable Viewer</h2>
      <CitationViewer
        v-if="showCloseable"
        :citations="multipleCitations"
        :confidence="0.85"
        :extracted-at="extractedTimestamp"
        closeable
        @close="showCloseable = false"
        @view-pdf="handleViewPdf"
      />
      <button
        v-else
        class="show-button"
        @click="showCloseable = true"
      >
        Show Citation Viewer
      </button>
    </section>

    <!-- Example 7: Without Confidence and Timestamp -->
    <section class="example-section">
      <h2 class="section-title">Example 7: Minimal Display</h2>
      <CitationViewer
        :citations="multipleCitations"
        :show-confidence="false"
        :show-timestamp="false"
      />
    </section>

    <!-- Example 8: Long Text Citation -->
    <section class="example-section">
      <h2 class="section-title">Example 8: Long Text Citation</h2>
      <CitationViewer
        :citations="longTextCitation"
        :confidence="0.95"
        :extracted-at="extractedTimestamp"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CitationViewer from './CitationViewer.vue'
import type { Citation } from '@/types'

// State
const showCloseable = ref(true)

// Sample data
const extractedTimestamp = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago

const multipleCitations: Citation[] = [
  {
    pdfName: 'RELIANCE/2024_BRSR.pdf',
    pages: [45, 46],
    chunkText:
      'Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e, representing a 5% reduction from the previous year. This reduction was achieved through improved energy efficiency measures and the adoption of cleaner fuel alternatives across our operations.',
    url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/45'
  },
  {
    pdfName: 'RELIANCE/2024_BRSR.pdf',
    pages: [47],
    chunkText:
      'The company has implemented a comprehensive carbon management strategy that includes regular monitoring, reporting, and verification of greenhouse gas emissions across all facilities.',
    url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/47'
  },
  {
    pdfName: 'RELIANCE/2024_Annual_Report.pdf',
    pages: [120, 121, 122],
    chunkText:
      'Environmental sustainability remains a core focus area. Our emissions reduction targets are aligned with the Paris Agreement goals, and we have committed to achieving net-zero emissions by 2050.',
    url: '/api/documents/RELIANCE/2024_Annual_Report.pdf/page/120'
  }
]

const singleCitation: Citation[] = [
  {
    pdfName: 'TCS/2024_BRSR.pdf',
    pages: [32],
    chunkText:
      'Total water consumption for the reporting period was 2.5 million cubic meters, with 60% sourced from recycled and rainwater harvesting systems.',
    url: '/api/documents/TCS/2024_BRSR.pdf/page/32'
  }
]

const longTextCitation: Citation[] = [
  {
    pdfName: 'INFOSYS/2024_BRSR.pdf',
    pages: [55, 56, 57, 58, 59],
    chunkText:
      'The company has established a robust governance framework for ESG management, which includes a dedicated ESG committee at the board level. This committee meets quarterly to review progress on sustainability initiatives, assess emerging risks and opportunities, and provide strategic guidance on ESG matters. The framework encompasses comprehensive policies on environmental management, social responsibility, and corporate governance. Key performance indicators are tracked regularly, and progress is reported transparently to all stakeholders through our annual sustainability report. Our commitment to ESG excellence is reflected in our inclusion in major sustainability indices and our recognition by leading ESG rating agencies. We continue to invest in innovative solutions that address environmental challenges while creating long-term value for our stakeholders. The integration of ESG considerations into our business strategy has enabled us to identify new opportunities, mitigate risks, and enhance our competitive position in the market.',
    url: '/api/documents/INFOSYS/2024_BRSR.pdf/page/55'
  }
]

// Event handlers
const handleViewPdf = (citation: Citation) => {
  console.log('View PDF clicked:', citation)
  alert(`Opening PDF: ${citation.pdfName} at page ${citation.pages[0]}`)
}

const handleRetry = () => {
  console.log('Retry clicked')
  alert('Retrying to load citations...')
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
  @apply space-y-4;
}

.section-title {
  @apply text-xl font-semibold text-gray-800;
}

.show-button {
  @apply px-4 py-2 bg-blue-600 text-white rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}
</style>
