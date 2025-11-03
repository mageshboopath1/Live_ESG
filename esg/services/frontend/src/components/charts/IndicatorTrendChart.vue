<template>
  <div class="indicator-trend-chart">
    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
    </div>
    <div v-else-if="!hasData" class="empty-state">
      <p class="empty-message">No historical data available for this indicator</p>
    </div>
    <div v-else class="chart-wrapper">
      <LineChart
        :labels="years"
        :datasets="datasets"
        :title="chartTitle"
        :y-axis-label="yAxisLabel"
        x-axis-label="Year"
        :y-min="0"
        :tooltip-callback="tooltipCallback"
      />
      <div v-if="showCitations && currentCitations.length > 0" class="citations-panel">
        <h4 class="citations-title">Source Citations</h4>
        <div class="citations-list">
          <button
            v-for="(citation, index) in currentCitations"
            :key="index"
            class="citation-item"
            @click="$emit('citation-click', citation)"
          >
            <svg class="citation-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span class="citation-text">{{ citation.pdfName }} (p. {{ citation.pages.join(', ') }})</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import LineChart from './LineChart.vue'
import LoadingSpinner from '../LoadingSpinner.vue'
import type { ExtractedIndicator, Citation } from '@/types'

interface Props {
  indicatorData: ExtractedIndicator[]
  indicatorName: string
  unit?: string
  showCitations?: boolean
  loading?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  unit: '',
  showCitations: true,
  loading: false,
  error: ''
})

const emit = defineEmits<{
  'citation-click': [citation: Citation]
}>()

const currentCitations = ref<Citation[]>([])

const hasData = computed(() => props.indicatorData.length > 0)

const sortedData = computed(() => {
  return [...props.indicatorData].sort((a, b) => a.report_year - b.report_year)
})

const years = computed(() => {
  return sortedData.value.map(d => d.report_year.toString())
})

const datasets = computed(() => {
  const data = sortedData.value.map(d => d.numeric_value || 0)
  
  return [
    {
      label: props.indicatorName,
      data,
      borderColor: '#6366F1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      fill: true,
      tension: 0.4
    }
  ]
})

const chartTitle = computed(() => {
  return `${props.indicatorName} Trend`
})

const yAxisLabel = computed(() => {
  return props.unit ? `Value (${props.unit})` : 'Value'
})

const tooltipCallback = (value: number, label: string, datasetLabel: string): string => {
  const year = parseInt(label)
  const dataPoint = sortedData.value.find(d => d.report_year === year)
  
  if (dataPoint && props.showCitations) {
    // Update current citations for display
    currentCitations.value = [{
      pdfName: dataPoint.object_key,
      pages: dataPoint.source_pages,
      chunkText: '',
      url: ''
    }]
  }
  
  const formattedValue = props.unit ? `${value.toFixed(2)} ${props.unit}` : value.toFixed(2)
  const confidence = dataPoint ? ` (Confidence: ${(dataPoint.confidence_score * 100).toFixed(0)}%)` : ''
  
  return `${datasetLabel}: ${formattedValue}${confidence}`
}
</script>

<style scoped>
.indicator-trend-chart {
  @apply w-full;
}

.loading-state,
.error-state,
.empty-state {
  @apply flex items-center justify-center py-12;
}

.error-message {
  @apply text-red-600 text-sm;
}

.empty-message {
  @apply text-gray-500 text-sm;
}

.chart-wrapper {
  @apply space-y-4;
}

.citations-panel {
  @apply bg-gray-50 rounded-lg p-4 border border-gray-200;
}

.citations-title {
  @apply text-sm font-semibold text-gray-700 mb-2;
}

.citations-list {
  @apply space-y-2;
}

.citation-item {
  @apply flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors;
  @apply w-full text-left;
}

.citation-icon {
  @apply w-4 h-4 flex-shrink-0;
}

.citation-text {
  @apply truncate;
}
</style>
