<template>
  <div class="score-visualization">
    <!-- Overall Score Section -->
    <div class="overall-score-section">
      <h2 class="section-title">Overall ESG Score</h2>
      <div class="overall-score-container">
        <div class="gauge-container">
          <Doughnut
            v-if="overallChartData"
            :data="overallChartData"
            :options="gaugeOptions"
            class="gauge-chart"
          />
          <div class="gauge-center">
            <div class="score-value">{{ formattedOverallScore }}</div>
            <div class="score-label">out of 100</div>
          </div>
        </div>
        <div v-if="scoreTrend" class="trend-indicator" :class="trendClass">
          <svg class="trend-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              v-if="scoreTrend.overall > 0"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
            <path
              v-else-if="scoreTrend.overall < 0"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
            />
            <path
              v-else
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 12h14"
            />
          </svg>
          <span class="trend-text">
            {{ trendText }}
          </span>
        </div>
      </div>
    </div>

    <!-- Pillar Scores Section -->
    <div class="pillar-scores-section">
      <h2 class="section-title">Pillar Scores</h2>
      <div class="pillar-grid">
        <!-- Environmental Pillar -->
        <div class="pillar-card pillar-environmental">
          <div class="pillar-header">
            <div class="pillar-icon-wrapper">
              <svg class="pillar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div class="pillar-info">
              <h3 class="pillar-name">Environmental</h3>
              <div class="pillar-score">{{ formattedEnvironmentalScore }}</div>
            </div>
          </div>
          <div class="progress-bar-container">
            <div
              class="progress-bar progress-environmental"
              :style="{ width: `${environmentalPercentage}%` }"
            ></div>
          </div>
          <div v-if="scoreTrend" class="pillar-trend" :class="getTrendClass(scoreTrend.environmental)">
            <svg class="trend-icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                v-if="scoreTrend.environmental > 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
              <path
                v-else-if="scoreTrend.environmental < 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
            <span>{{ formatTrendValue(scoreTrend.environmental) }}</span>
          </div>
        </div>

        <!-- Social Pillar -->
        <div class="pillar-card pillar-social">
          <div class="pillar-header">
            <div class="pillar-icon-wrapper">
              <svg class="pillar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <div class="pillar-info">
              <h3 class="pillar-name">Social</h3>
              <div class="pillar-score">{{ formattedSocialScore }}</div>
            </div>
          </div>
          <div class="progress-bar-container">
            <div
              class="progress-bar progress-social"
              :style="{ width: `${socialPercentage}%` }"
            ></div>
          </div>
          <div v-if="scoreTrend" class="pillar-trend" :class="getTrendClass(scoreTrend.social)">
            <svg class="trend-icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                v-if="scoreTrend.social > 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
              <path
                v-else-if="scoreTrend.social < 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
            <span>{{ formatTrendValue(scoreTrend.social) }}</span>
          </div>
        </div>

        <!-- Governance Pillar -->
        <div class="pillar-card pillar-governance">
          <div class="pillar-header">
            <div class="pillar-icon-wrapper">
              <svg class="pillar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <div class="pillar-info">
              <h3 class="pillar-name">Governance</h3>
              <div class="pillar-score">{{ formattedGovernanceScore }}</div>
            </div>
          </div>
          <div class="progress-bar-container">
            <div
              class="progress-bar progress-governance"
              :style="{ width: `${governancePercentage}%` }"
            ></div>
          </div>
          <div v-if="scoreTrend" class="pillar-trend" :class="getTrendClass(scoreTrend.governance)">
            <svg class="trend-icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                v-if="scoreTrend.governance > 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
              <path
                v-else-if="scoreTrend.governance < 0"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
            <span>{{ formatTrendValue(scoreTrend.governance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Multi-Year Trend Section -->
    <div v-if="showTrend && scoreHistory.length > 1" class="trend-section">
      <h2 class="section-title">Score Trends</h2>
      <div class="chart-container">
        <Line
          v-if="trendChartData"
          :data="trendChartData"
          :options="trendChartOptions"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartData,
  type ChartOptions
} from 'chart.js'
import type { ESGScore } from '@/types'

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Props
interface Props {
  score: ESGScore | null
  scoreHistory?: ESGScore[]
  showTrend?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  scoreHistory: () => [],
  showTrend: true
})

// Computed - Score values
const formattedOverallScore = computed(() => {
  return props.score?.overall_score?.toFixed(1) || '0.0'
})

const formattedEnvironmentalScore = computed(() => {
  return props.score?.environmental_score?.toFixed(1) || '0.0'
})

const formattedSocialScore = computed(() => {
  return props.score?.social_score?.toFixed(1) || '0.0'
})

const formattedGovernanceScore = computed(() => {
  return props.score?.governance_score?.toFixed(1) || '0.0'
})

// Computed - Percentages for progress bars
const environmentalPercentage = computed(() => {
  return props.score?.environmental_score || 0
})

const socialPercentage = computed(() => {
  return props.score?.social_score || 0
})

const governancePercentage = computed(() => {
  return props.score?.governance_score || 0
})

// Computed - Score trend
const scoreTrend = computed(() => {
  if (!props.scoreHistory || props.scoreHistory.length < 2) return null

  const sorted = [...props.scoreHistory].sort((a, b) => a.report_year - b.report_year)
  const first = sorted[0]
  const last = sorted[sorted.length - 1]

  return {
    environmental: last.environmental_score - first.environmental_score,
    social: last.social_score - first.social_score,
    governance: last.governance_score - first.governance_score,
    overall: last.overall_score - first.overall_score,
    years: last.report_year - first.report_year
  }
})

const trendClass = computed(() => {
  if (!scoreTrend.value) return ''
  if (scoreTrend.value.overall > 0) return 'trend-positive'
  if (scoreTrend.value.overall < 0) return 'trend-negative'
  return 'trend-neutral'
})

const trendText = computed(() => {
  if (!scoreTrend.value) return ''
  const change = Math.abs(scoreTrend.value.overall).toFixed(1)
  const direction = scoreTrend.value.overall > 0 ? 'increase' : scoreTrend.value.overall < 0 ? 'decrease' : 'no change'
  const years = scoreTrend.value.years > 1 ? `${scoreTrend.value.years} years` : 'year'
  
  if (direction === 'no change') {
    return `No change over ${years}`
  }
  
  return `${change} point ${direction} over ${years}`
})

// Methods
const getTrendClass = (value: number): string => {
  if (value > 0) return 'trend-positive'
  if (value < 0) return 'trend-negative'
  return 'trend-neutral'
}

const formatTrendValue = (value: number): string => {
  const formatted = Math.abs(value).toFixed(1)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return '0.0'
}

// Chart data - Overall gauge
const overallChartData = computed<ChartData<'doughnut'> | null>(() => {
  if (!props.score) return null

  const score = props.score.overall_score
  const remaining = 100 - score

  return {
    labels: ['Score', 'Remaining'],
    datasets: [
      {
        data: [score, remaining],
        backgroundColor: [
          getScoreColor(score),
          '#E5E7EB'
        ],
        borderWidth: 0,
        circumference: 180,
        rotation: 270
      }
    ]
  }
})

const gaugeOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  cutout: '75%',
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      enabled: false
    }
  }
}))

// Chart data - Trend line chart
const trendChartData = computed<ChartData<'line'> | null>(() => {
  if (!props.scoreHistory || props.scoreHistory.length < 2) return null

  const sorted = [...props.scoreHistory].sort((a, b) => a.report_year - b.report_year)
  const years = sorted.map(s => s.report_year.toString())

  return {
    labels: years,
    datasets: [
      {
        label: 'Overall ESG',
        data: sorted.map(s => s.overall_score),
        borderColor: '#6366F1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Environmental',
        data: sorted.map(s => s.environmental_score),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Social',
        data: sorted.map(s => s.social_score),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Governance',
        data: sorted.map(s => s.governance_score),
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.4,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ]
  }
})

const trendChartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: true,
      position: 'bottom',
      labels: {
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: (context) => {
          const value = context.parsed.y
          return `${context.dataset.label}: ${value !== null ? value.toFixed(1) : 'N/A'}`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      ticks: {
        callback: (value) => `${value}`
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    },
    x: {
      grid: {
        display: false
      }
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
}))

// Helper function to get color based on score
const getScoreColor = (score: number): string => {
  if (score >= 80) return '#10B981' // Green
  if (score >= 60) return '#F59E0B' // Yellow
  if (score >= 40) return '#F97316' // Orange
  return '#EF4444' // Red
}
</script>

<style scoped>
.score-visualization {
  @apply space-y-8;
}

/* Section Titles */
.section-title {
  @apply text-2xl font-bold text-gray-900 mb-6;
}

/* Overall Score Section */
.overall-score-section {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.overall-score-container {
  @apply flex flex-col items-center gap-6;
}

.gauge-container {
  @apply relative w-64 h-32;
}

.gauge-chart {
  @apply w-full h-full;
}

.gauge-center {
  @apply absolute top-1/2 left-1/2 transform -translate-x-1/2 translate-y-1/4;
  @apply text-center;
}

.score-value {
  @apply text-4xl font-bold text-gray-900;
}

.score-label {
  @apply text-sm text-gray-600 mt-1;
}

/* Trend Indicator */
.trend-indicator {
  @apply flex items-center gap-2 px-4 py-2 rounded-full;
}

.trend-positive {
  @apply bg-green-100 text-green-800;
}

.trend-negative {
  @apply bg-red-100 text-red-800;
}

.trend-neutral {
  @apply bg-gray-100 text-gray-800;
}

.trend-icon {
  @apply w-5 h-5;
}

.trend-text {
  @apply text-sm font-medium;
}

/* Pillar Scores Section */
.pillar-scores-section {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.pillar-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-6;
}

.pillar-card {
  @apply bg-gradient-to-br rounded-lg p-6 space-y-4;
}

.pillar-environmental {
  @apply from-green-50 to-green-100 border border-green-200;
}

.pillar-social {
  @apply from-blue-50 to-blue-100 border border-blue-200;
}

.pillar-governance {
  @apply from-purple-50 to-purple-100 border border-purple-200;
}

.pillar-header {
  @apply flex items-start gap-4;
}

.pillar-icon-wrapper {
  @apply flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center;
}

.pillar-environmental .pillar-icon-wrapper {
  @apply bg-green-500;
}

.pillar-social .pillar-icon-wrapper {
  @apply bg-blue-500;
}

.pillar-governance .pillar-icon-wrapper {
  @apply bg-purple-500;
}

.pillar-icon {
  @apply w-6 h-6 text-white;
}

.pillar-info {
  @apply flex-1;
}

.pillar-name {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.pillar-score {
  @apply text-3xl font-bold text-gray-900;
}

/* Progress Bar */
.progress-bar-container {
  @apply w-full h-3 bg-white rounded-full overflow-hidden;
}

.progress-bar {
  @apply h-full rounded-full transition-all duration-500 ease-out;
}

.progress-environmental {
  @apply bg-green-500;
}

.progress-social {
  @apply bg-blue-500;
}

.progress-governance {
  @apply bg-purple-500;
}

/* Pillar Trend */
.pillar-trend {
  @apply flex items-center gap-1.5 text-sm font-medium;
}

.trend-icon-small {
  @apply w-4 h-4;
}

/* Trend Section */
.trend-section {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.chart-container {
  @apply w-full h-80;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .pillar-grid {
    @apply grid-cols-1;
  }
  
  .gauge-container {
    @apply w-48 h-24;
  }
  
  .score-value {
    @apply text-3xl;
  }
  
  .chart-container {
    @apply h-64;
  }
}
</style>
