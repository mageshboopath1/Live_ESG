<template>
  <div class="multi-indicator-chart">
    <div class="chart-controls">
      <div class="control-group">
        <label class="control-label">Chart Type</label>
        <select v-model="chartType" class="control-select">
          <option value="line">Line Chart</option>
          <option value="bar">Bar Chart</option>
        </select>
      </div>
      <div v-if="years.length > 0" class="control-group">
        <label class="control-label">Year</label>
        <select v-model="selectedYear" class="control-select">
          <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
    </div>
    <div v-else-if="!hasData" class="empty-state">
      <p class="empty-message">No indicator data available</p>
    </div>
    <div v-else class="chart-container">
      <LineChart
        v-if="chartType === 'line'"
        :labels="indicatorLabels"
        :datasets="lineDatasets"
        :title="chartTitle"
        y-axis-label="Value"
        x-axis-label="Indicator"
        :tooltip-callback="tooltipCallback"
      />
      <BarChart
        v-else
        :labels="indicatorLabels"
        :datasets="barDatasets"
        :title="chartTitle"
        y-axis-label="Value"
        x-axis-label="Indicator"
        :tooltip-callback="tooltipCallback"
      />
    </div>

    <div v-if="showLegend && selectedIndicators.length > 0" class="legend-panel">
      <h4 class="legend-title">Indicators</h4>
      <div class="legend-grid">
        <div
          v-for="indicator in selectedIndicators"
          :key="indicator.id"
          class="legend-item"
        >
          <div class="legend-color" :style="{ backgroundColor: getIndicatorColor(indicator.pillar) }"></div>
          <div class="legend-info">
            <span class="legend-name">{{ indicator.name }}</span>
            <span class="legend-meta">{{ indicator.unit }} • {{ indicator.pillar }} Pillar</span>
          </div>
          <button
            v-if="indicator.citations"
            class="legend-citation"
            @click="$emit('indicator-click', indicator)"
          >
            <svg class="citation-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import LineChart from './LineChart.vue'
import BarChart from './BarChart.vue'
import LoadingSpinner from '../LoadingSpinner.vue'
import type { ExtractedIndicator, BRSRIndicatorDefinition } from '@/types'

interface IndicatorWithMeta extends ExtractedIndicator {
  name: string
  unit: string
  pillar: 'E' | 'S' | 'G'
  citations?: any[]
}

interface Props {
  indicators: IndicatorWithMeta[]
  definitions?: BRSRIndicatorDefinition[]
  showLegend?: boolean
  loading?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  definitions: () => [],
  showLegend: true,
  loading: false,
  error: ''
})

const emit = defineEmits<{
  'indicator-click': [indicator: IndicatorWithMeta]
}>()

const chartType = ref<'line' | 'bar'>('bar')
const selectedYear = ref<number | null>(null)

const hasData = computed(() => props.indicators.length > 0)

const years = computed(() => {
  const yearSet = new Set(props.indicators.map(i => i.report_year))
  return Array.from(yearSet).sort((a, b) => b - a)
})

// Initialize selected year
if (years.value.length > 0 && !selectedYear.value) {
  selectedYear.value = years.value[0]
}

const selectedIndicators = computed(() => {
  if (!selectedYear.value) return []
  return props.indicators.filter(i => i.report_year === selectedYear.value)
})

const indicatorLabels = computed(() => {
  return selectedIndicators.value.map(i => i.name || i.indicator_id.toString())
})

const lineDatasets = computed(() => {
  const groupedByPillar = selectedIndicators.value.reduce((acc, indicator) => {
    const pillar = indicator.pillar
    if (!acc[pillar]) {
      acc[pillar] = []
    }
    acc[pillar].push(indicator.numeric_value || 0)
    return acc
  }, {} as Record<string, number[]>)

  return Object.entries(groupedByPillar).map(([pillar, data]) => ({
    label: `${pillar} Pillar`,
    data,
    borderColor: getIndicatorColor(pillar as 'E' | 'S' | 'G'),
    backgroundColor: getIndicatorColor(pillar as 'E' | 'S' | 'G', 0.1),
    fill: false,
    tension: 0.4
  }))
})

const barDatasets = computed(() => {
  return [{
    label: 'Indicator Values',
    data: selectedIndicators.value.map(i => i.numeric_value || 0),
    backgroundColor: selectedIndicators.value.map(i => getIndicatorColor(i.pillar, 0.8)),
    borderColor: selectedIndicators.value.map(i => getIndicatorColor(i.pillar)),
    borderWidth: 1
  }]
})

const chartTitle = computed(() => {
  if (!selectedYear.value) return 'Indicator Comparison'
  return `Indicator Comparison (${selectedYear.value})`
})

const getIndicatorColor = (pillar: 'E' | 'S' | 'G', alpha: number = 1): string => {
  const colors = {
    E: { r: 16, g: 185, b: 129 },   // Green
    S: { r: 59, g: 130, b: 246 },   // Blue
    G: { r: 139, g: 92, b: 246 }    // Purple
  }
  
  const color = colors[pillar]
  return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`
}

const tooltipCallback = (value: number, label: string, datasetLabel: string): string => {
  const indicator = selectedIndicators.value.find(i => (i.name || i.indicator_id.toString()) === label)
  
  if (!indicator) return `${datasetLabel}: ${value.toFixed(2)}`
  
  const unit = indicator.unit ? ` ${indicator.unit}` : ''
  const confidence = ` (${(indicator.confidence_score * 100).toFixed(0)}% confidence)`
  
  return `${label}: ${value.toFixed(2)}${unit}${confidence}`
}
</script>

<style scoped>
.multi-indicator-chart {
  @apply w-full space-y-4;
}

.chart-controls {
  @apply flex flex-wrap gap-4 items-end;
}

.control-group {
  @apply flex flex-col gap-1;
}

.control-label {
  @apply text-sm font-medium text-gray-700;
}

.control-select {
  @apply px-3 py-2 border border-gray-300 rounded-md text-sm;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
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

.chart-container {
  @apply bg-white rounded-lg p-4 border border-gray-200;
}

.legend-panel {
  @apply bg-gray-50 rounded-lg p-4 border border-gray-200;
}

.legend-title {
  @apply text-sm font-semibold text-gray-700 mb-3;
}

.legend-grid {
  @apply space-y-2;
}

.legend-item {
  @apply flex items-center gap-3 p-2 rounded hover:bg-white transition-colors;
}

.legend-color {
  @apply w-3 h-3 rounded-full flex-shrink-0;
}

.legend-info {
  @apply flex-1 flex flex-col;
}

.legend-name {
  @apply text-sm font-medium text-gray-900;
}

.legend-meta {
  @apply text-xs text-gray-500;
}

.legend-citation {
  @apply text-blue-600 hover:text-blue-800 transition-colors;
}

.citation-icon {
  @apply w-4 h-4;
}
</style>
