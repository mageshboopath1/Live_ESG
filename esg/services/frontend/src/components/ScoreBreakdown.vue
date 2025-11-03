<template>
  <div class="score-breakdown">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="loading-text">Loading score breakdown...</p>
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
    </div>

    <!-- Breakdown Content -->
    <div v-else-if="breakdown" class="breakdown-content">
      <!-- Overall Score Section -->
      <div class="overall-section">
        <div class="section-header">
          <h2 class="section-title">Overall ESG Score</h2>
          <div class="overall-score-badge">
            {{ formattedOverallScore }}
          </div>
        </div>
        <p class="section-description">
          The overall ESG score is calculated by combining the three pillar scores with their respective weights.
        </p>
      </div>

      <!-- Pillars Section -->
      <div class="pillars-section">
        <h3 class="subsection-title">Pillar Breakdown</h3>
        
        <div class="pillars-grid">
          <div
            v-for="pillar in breakdown.pillars"
            :key="pillar.name"
            class="pillar-breakdown-card"
            :class="`pillar-${pillar.name.toLowerCase()}`"
          >
            <!-- Pillar Header -->
            <div class="pillar-breakdown-header">
              <div class="pillar-info-row">
                <div class="pillar-icon-wrapper" :class="`icon-${pillar.name.toLowerCase()}`">
                  <svg
                    v-if="pillar.name === 'Environmental'"
                    class="pillar-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <svg
                    v-else-if="pillar.name === 'Social'"
                    class="pillar-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="pillar-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <div class="pillar-title-group">
                  <h4 class="pillar-title">{{ pillar.name }}</h4>
                  <div class="pillar-weight-badge">
                    Weight: {{ formatPercentage(pillar.weight) }}
                  </div>
                </div>
              </div>
              <div class="pillar-score-display">
                {{ pillar.score.toFixed(1) }}
              </div>
            </div>

            <!-- Pillar Indicators -->
            <div class="pillar-indicators">
              <div class="indicators-header">
                <span class="indicators-label">Contributing Indicators</span>
                <span class="indicators-count">{{ pillar.indicators.length }}</span>
              </div>
              
              <div class="indicators-list">
                <button
                  v-for="indicator in pillar.indicators"
                  :key="indicator.code"
                  class="indicator-item"
                  @click="handleIndicatorClick(indicator)"
                  @keypress.enter="handleIndicatorClick(indicator)"
                >
                  <div class="indicator-item-header">
                    <span class="indicator-code">{{ indicator.code }}</span>
                    <span class="indicator-value">{{ formatValue(indicator.value) }}</span>
                  </div>
                  <div class="indicator-item-footer">
                    <div class="indicator-weight">
                      <svg class="weight-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                        />
                      </svg>
                      <span>{{ formatPercentage(indicator.weight) }}</span>
                    </div>
                    <div v-if="indicator.citations && indicator.citations.length > 0" class="indicator-citations">
                      <svg class="citation-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span>{{ formatCitationPages(indicator.citations) }}</span>
                    </div>
                  </div>
                  <svg class="indicator-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          </div>
        </div>
      </div>

      <!-- Calculation Methodology -->
      <div class="methodology-section">
        <button
          class="methodology-toggle"
          @click="showMethodology = !showMethodology"
          @keypress.enter="showMethodology = !showMethodology"
        >
          <svg
            class="toggle-icon"
            :class="{ 'rotate-90': showMethodology }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
          <span class="methodology-title">Calculation Methodology</span>
        </button>
        
        <div v-if="showMethodology" class="methodology-content">
          <p class="methodology-text">
            The ESG score is calculated using a weighted aggregation approach:
          </p>
          <ol class="methodology-list">
            <li>Each indicator is assigned a weight based on its importance within its pillar</li>
            <li>Pillar scores are calculated by aggregating weighted indicator values</li>
            <li>The overall ESG score combines the three pillar scores with configurable weights</li>
            <li>All values are normalized to a 0-100 scale for consistency</li>
          </ol>
          <div class="methodology-formula">
            <code class="formula-text">
              ESG Score = (E × {{ formatPercentage(getWeight('Environmental')) }}) + 
              (S × {{ formatPercentage(getWeight('Social')) }}) + 
              (G × {{ formatPercentage(getWeight('Governance')) }})
            </code>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <p class="empty-text">No score breakdown available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ScoreBreakdown, IndicatorContribution, Citation } from '@/types'

// Props
interface Props {
  breakdown: ScoreBreakdown | null
  overallScore?: number
  loading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  overallScore: 0,
  loading: false,
  error: null
})

// Emits
const emit = defineEmits<{
  (e: 'indicatorClick', indicator: IndicatorContribution): void
}>()

// State
const showMethodology = ref(false)

// Computed
const formattedOverallScore = computed(() => {
  return props.overallScore.toFixed(1)
})

// Methods
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(0)}%`
}

const formatValue = (value: number): string => {
  if (value === null || value === undefined) return 'N/A'
  
  // Format large numbers with commas
  if (value >= 1000) {
    return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
  }
  
  return value.toFixed(2)
}

const formatCitationPages = (citations: Citation[]): string => {
  if (!citations || citations.length === 0) return ''
  
  const allPages = citations.flatMap(c => c.pages)
  const uniquePages = [...new Set(allPages)].sort((a, b) => a - b)
  
  if (uniquePages.length === 0) return ''
  if (uniquePages.length === 1) return `Page ${uniquePages[0]}`
  if (uniquePages.length === 2) return `Pages ${uniquePages.join(', ')}`
  
  return `Pages ${uniquePages[0]}, ..., ${uniquePages[uniquePages.length - 1]}`
}

const getWeight = (pillarName: string): number => {
  if (!props.breakdown) return 0
  const pillar = props.breakdown.pillars.find(p => p.name === pillarName)
  return pillar?.weight || 0
}

const handleIndicatorClick = (indicator: IndicatorContribution) => {
  emit('indicatorClick', indicator)
}
</script>

<style scoped>
.score-breakdown {
  @apply space-y-6;
}

/* Loading State */
.loading-container {
  @apply flex flex-col items-center justify-center py-12 space-y-4;
}

.spinner {
  @apply w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin;
}

.loading-text {
  @apply text-gray-600 text-sm;
}

/* Error State */
.error-container {
  @apply flex flex-col items-center justify-center py-12 space-y-4;
  @apply bg-red-50 border border-red-200 rounded-lg;
}

.error-icon {
  @apply w-12 h-12 text-red-500;
}

.error-text {
  @apply text-red-700 text-sm;
}

/* Empty State */
.empty-state {
  @apply flex flex-col items-center justify-center py-12 space-y-4;
  @apply bg-gray-50 border border-gray-200 rounded-lg;
}

.empty-icon {
  @apply w-12 h-12 text-gray-400;
}

.empty-text {
  @apply text-gray-600 text-sm;
}

/* Overall Section */
.overall-section {
  @apply bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6;
  @apply border border-blue-200;
}

.section-header {
  @apply flex items-center justify-between mb-3;
}

.section-title {
  @apply text-2xl font-bold text-gray-900;
}

.overall-score-badge {
  @apply px-4 py-2 bg-white rounded-full;
  @apply text-3xl font-bold text-blue-600;
  @apply shadow-sm border border-blue-200;
}

.section-description {
  @apply text-sm text-gray-700;
}

/* Pillars Section */
.pillars-section {
  @apply space-y-4;
}

.subsection-title {
  @apply text-xl font-bold text-gray-900;
}

.pillars-grid {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-6;
}

/* Pillar Breakdown Card */
.pillar-breakdown-card {
  @apply bg-white rounded-lg shadow-sm border;
  @apply overflow-hidden;
}

.pillar-environmental {
  @apply border-green-200;
}

.pillar-social {
  @apply border-blue-200;
}

.pillar-governance {
  @apply border-purple-200;
}

.pillar-breakdown-header {
  @apply p-4 border-b border-gray-100;
}

.pillar-info-row {
  @apply flex items-start gap-3 mb-3;
}

.pillar-icon-wrapper {
  @apply flex-shrink-0 w-10 h-10 rounded-full;
  @apply flex items-center justify-center;
}

.icon-environmental {
  @apply bg-green-500;
}

.icon-social {
  @apply bg-blue-500;
}

.icon-governance {
  @apply bg-purple-500;
}

.pillar-icon {
  @apply w-5 h-5 text-white;
}

.pillar-title-group {
  @apply flex-1;
}

.pillar-title {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.pillar-weight-badge {
  @apply inline-block px-2 py-0.5 text-xs font-medium;
  @apply bg-gray-100 text-gray-700 rounded;
}

.pillar-score-display {
  @apply text-3xl font-bold text-gray-900;
}

/* Pillar Indicators */
.pillar-indicators {
  @apply p-4 space-y-3;
}

.indicators-header {
  @apply flex items-center justify-between mb-2;
}

.indicators-label {
  @apply text-sm font-medium text-gray-700;
}

.indicators-count {
  @apply px-2 py-0.5 text-xs font-medium;
  @apply bg-gray-100 text-gray-600 rounded-full;
}

.indicators-list {
  @apply space-y-2;
}

/* Indicator Item */
.indicator-item {
  @apply w-full relative;
  @apply bg-gray-50 hover:bg-gray-100 rounded-lg p-3;
  @apply border border-gray-200 hover:border-gray-300;
  @apply transition-all duration-150;
  @apply cursor-pointer;
  @apply text-left;
  @apply pr-8;
}

.indicator-item:focus {
  @apply outline-none ring-2 ring-blue-500 ring-offset-1;
}

.indicator-item-header {
  @apply flex items-center justify-between mb-2;
}

.indicator-code {
  @apply text-sm font-mono font-medium text-gray-900;
}

.indicator-value {
  @apply text-sm font-semibold text-gray-900;
}

.indicator-item-footer {
  @apply flex items-center gap-3 text-xs text-gray-600;
}

.indicator-weight,
.indicator-citations {
  @apply flex items-center gap-1;
}

.weight-icon,
.citation-icon {
  @apply w-3.5 h-3.5;
}

.indicator-arrow {
  @apply absolute right-2 top-1/2 transform -translate-y-1/2;
  @apply w-4 h-4 text-gray-400;
  @apply transition-all duration-150;
}

.indicator-item:hover .indicator-arrow {
  @apply text-blue-600 translate-x-0.5;
}

/* Methodology Section */
.methodology-section {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden;
}

.methodology-toggle {
  @apply w-full flex items-center gap-3 p-4;
  @apply text-left hover:bg-gray-50 transition-colors duration-150;
  @apply focus:outline-none focus:bg-gray-50;
  @apply cursor-pointer;
}

.toggle-icon {
  @apply w-5 h-5 text-gray-500 transition-transform duration-200;
}

.rotate-90 {
  transform: rotate(90deg);
}

.methodology-title {
  @apply text-lg font-semibold text-gray-900;
}

.methodology-content {
  @apply px-4 pb-4 space-y-4;
}

.methodology-text {
  @apply text-sm text-gray-700;
}

.methodology-list {
  @apply list-decimal list-inside space-y-2 text-sm text-gray-700;
}

.methodology-formula {
  @apply bg-gray-50 rounded-lg p-4 border border-gray-200;
}

.formula-text {
  @apply text-xs font-mono text-gray-800 break-all;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .pillars-grid {
    @apply grid-cols-1;
  }
}
</style>
