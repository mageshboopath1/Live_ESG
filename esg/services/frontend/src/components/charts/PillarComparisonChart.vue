<template>
  <div class="pillar-comparison-chart">
    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
    </div>
    <div v-else-if="!hasData" class="empty-state">
      <p class="empty-message">No score data available</p>
    </div>
    <div v-else class="chart-wrapper">
      <RadarChart
        :labels="pillarLabels"
        :datasets="datasets"
        :title="chartTitle"
        :max="100"
        :tooltip-callback="tooltipCallback"
      />
      <div v-if="showBreakdown" class="breakdown-panel">
        <h4 class="breakdown-title">Score Breakdown</h4>
        <div class="breakdown-grid">
          <div
            v-for="(pillar, index) in pillarBreakdown"
            :key="index"
            class="breakdown-item"
          >
            <div class="breakdown-header">
              <span class="breakdown-label">{{ pillar.label }}</span>
              <span class="breakdown-score">{{ pillar.score.toFixed(1) }}</span>
            </div>
            <div class="breakdown-bar-container">
              <div
                class="breakdown-bar"
                :style="{
                  width: `${pillar.score}%`,
                  backgroundColor: pillar.color
                }"
              ></div>
            </div>
            <button
              v-if="pillar.citations.length > 0"
              class="breakdown-citations"
              @click="$emit('pillar-click', pillar.pillar)"
            >
              <svg class="citation-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{{ pillar.citations.length }} source{{ pillar.citations.length > 1 ? 's' : '' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import RadarChart from './RadarChart.vue'
import LoadingSpinner from '../LoadingSpinner.vue'
import type { ESGScore } from '@/types'

interface Props {
  scores: ESGScore[]
  companyNames?: string[]
  showBreakdown?: boolean
  loading?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  companyNames: () => [],
  showBreakdown: true,
  loading: false,
  error: ''
})

const emit = defineEmits<{
  'pillar-click': [pillar: 'E' | 'S' | 'G']
}>()

const hasData = computed(() => props.scores.length > 0)

const pillarLabels = computed(() => [
  'Environmental',
  'Social',
  'Governance'
])

const datasets = computed(() => {
  const colors = [
    { border: '#10B981', background: 'rgba(16, 185, 129, 0.2)' },
    { border: '#3B82F6', background: 'rgba(59, 130, 246, 0.2)' },
    { border: '#8B5CF6', background: 'rgba(139, 92, 246, 0.2)' },
    { border: '#F59E0B', background: 'rgba(245, 158, 11, 0.2)' }
  ]

  return props.scores.map((score, index) => {
    const color = colors[index % colors.length]
    const label = props.companyNames[index] || `Company ${index + 1}`

    return {
      label,
      data: [
        score.environmental_score,
        score.social_score,
        score.governance_score
      ],
      borderColor: color.border,
      backgroundColor: color.background
    }
  })
})

const chartTitle = computed(() => {
  if (props.scores.length === 1) {
    return 'ESG Pillar Scores'
  }
  return 'ESG Pillar Comparison'
})

const pillarBreakdown = computed(() => {
  if (props.scores.length === 0) return []

  const score = props.scores[0]
  const metadata = score.calculation_metadata

  return [
    {
      label: 'Environmental',
      pillar: 'E' as const,
      score: score.environmental_score,
      color: '#10B981',
      citations: getIndicatorsForPillar(metadata, 'E')
    },
    {
      label: 'Social',
      pillar: 'S' as const,
      score: score.social_score,
      color: '#3B82F6',
      citations: getIndicatorsForPillar(metadata, 'S')
    },
    {
      label: 'Governance',
      pillar: 'G' as const,
      score: score.governance_score,
      color: '#8B5CF6',
      citations: getIndicatorsForPillar(metadata, 'G')
    }
  ]
})

const getIndicatorsForPillar = (metadata: any, pillar: 'E' | 'S' | 'G') => {
  if (!metadata?.indicators) return []
  
  return Object.entries(metadata.indicators)
    .filter(([_, indicator]: [string, any]) => indicator.pillar === pillar)
    .map(([code]) => code)
}

const tooltipCallback = (value: number, label: string, datasetLabel: string): string => {
  return `${datasetLabel} - ${label}: ${value.toFixed(1)}`
}
</script>

<style scoped>
.pillar-comparison-chart {
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
  @apply space-y-6;
}

.breakdown-panel {
  @apply bg-gray-50 rounded-lg p-4 border border-gray-200;
}

.breakdown-title {
  @apply text-sm font-semibold text-gray-700 mb-4;
}

.breakdown-grid {
  @apply space-y-4;
}

.breakdown-item {
  @apply space-y-2;
}

.breakdown-header {
  @apply flex items-center justify-between;
}

.breakdown-label {
  @apply text-sm font-medium text-gray-700;
}

.breakdown-score {
  @apply text-sm font-bold text-gray-900;
}

.breakdown-bar-container {
  @apply w-full h-2 bg-gray-200 rounded-full overflow-hidden;
}

.breakdown-bar {
  @apply h-full rounded-full transition-all duration-500 ease-out;
}

.breakdown-citations {
  @apply flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 transition-colors;
}

.citation-icon {
  @apply w-3.5 h-3.5;
}
</style>
