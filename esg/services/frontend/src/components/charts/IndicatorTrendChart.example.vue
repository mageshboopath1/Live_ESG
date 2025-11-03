<template>
  <div class="example-container">
    <h1 class="example-title">Indicator Trend Chart Examples</h1>

    <section class="example-section">
      <h2 class="section-title">Single Indicator Trend</h2>
      <p class="section-description">
        Shows how an indicator value changes over multiple years with confidence scores and citations.
      </p>
      <div class="chart-wrapper">
        <IndicatorTrendChart
          :indicator-data="emissionsData"
          indicator-name="Total Scope 1 Emissions"
          unit="MT CO2e"
          @citation-click="handleCitationClick"
        />
      </div>
    </section>

    <section class="example-section">
      <h2 class="section-title">Water Consumption Trend</h2>
      <p class="section-description">
        Another example showing water consumption over time.
      </p>
      <div class="chart-wrapper">
        <IndicatorTrendChart
          :indicator-data="waterData"
          indicator-name="Total Water Consumption"
          unit="KL"
          @citation-click="handleCitationClick"
        />
      </div>
    </section>

    <section class="example-section">
      <h2 class="section-title">Loading State</h2>
      <div class="chart-wrapper">
        <IndicatorTrendChart
          :indicator-data="[]"
          indicator-name="Loading Indicator"
          :loading="true"
        />
      </div>
    </section>

    <section class="example-section">
      <h2 class="section-title">Error State</h2>
      <div class="chart-wrapper">
        <IndicatorTrendChart
          :indicator-data="[]"
          indicator-name="Error Indicator"
          error="Failed to load indicator data"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import IndicatorTrendChart from './IndicatorTrendChart.vue'
import type { ExtractedIndicator, Citation } from '@/types'

// Sample data for emissions
const emissionsData: ExtractedIndicator[] = [
  {
    id: 1,
    object_key: 'RELIANCE/2020_BRSR.pdf',
    company_id: 1,
    report_year: 2020,
    indicator_id: 1,
    extracted_value: '1150',
    numeric_value: 1150,
    confidence_score: 0.92,
    validation_status: 'valid',
    source_pages: [45],
    source_chunk_ids: [123],
    extracted_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 2,
    object_key: 'RELIANCE/2021_BRSR.pdf',
    company_id: 1,
    report_year: 2021,
    indicator_id: 1,
    extracted_value: '1200',
    numeric_value: 1200,
    confidence_score: 0.95,
    validation_status: 'valid',
    source_pages: [46],
    source_chunk_ids: [124],
    extracted_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 3,
    object_key: 'RELIANCE/2022_BRSR.pdf',
    company_id: 1,
    report_year: 2022,
    indicator_id: 1,
    extracted_value: '1180',
    numeric_value: 1180,
    confidence_score: 0.94,
    validation_status: 'valid',
    source_pages: [47],
    source_chunk_ids: [125],
    extracted_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 4,
    object_key: 'RELIANCE/2023_BRSR.pdf',
    company_id: 1,
    report_year: 2023,
    indicator_id: 1,
    extracted_value: '1100',
    numeric_value: 1100,
    confidence_score: 0.96,
    validation_status: 'valid',
    source_pages: [48],
    source_chunk_ids: [126],
    extracted_at: '2024-01-15T10:00:00Z'
  }
]

// Sample data for water consumption
const waterData: ExtractedIndicator[] = [
  {
    id: 5,
    object_key: 'RELIANCE/2020_BRSR.pdf',
    company_id: 1,
    report_year: 2020,
    indicator_id: 2,
    extracted_value: '50000',
    numeric_value: 50000,
    confidence_score: 0.89,
    validation_status: 'valid',
    source_pages: [52],
    source_chunk_ids: [130],
    extracted_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 6,
    object_key: 'RELIANCE/2021_BRSR.pdf',
    company_id: 1,
    report_year: 2021,
    indicator_id: 2,
    extracted_value: '48000',
    numeric_value: 48000,
    confidence_score: 0.91,
    validation_status: 'valid',
    source_pages: [53],
    source_chunk_ids: [131],
    extracted_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 7,
    object_key: 'RELIANCE/2022_BRSR.pdf',
    company_id: 1,
    report_year: 2022,
    indicator_id: 2,
    extracted_value: '46000',
    numeric_value: 46000,
    confidence_score: 0.93,
    validation_status: 'valid',
    source_pages: [54],
    source_chunk_ids: [132],
    extracted_at: '2024-01-15T10:00:00Z'
  }
]

const handleCitationClick = (citation: Citation) => {
  console.log('Citation clicked:', citation)
  alert(`Opening PDF: ${citation.pdfName}, Page: ${citation.pages.join(', ')}`)
}
</script>

<style scoped>
.example-container {
  @apply max-w-6xl mx-auto p-6 space-y-8;
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

.section-description {
  @apply text-sm text-gray-600;
}

.chart-wrapper {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}
</style>
