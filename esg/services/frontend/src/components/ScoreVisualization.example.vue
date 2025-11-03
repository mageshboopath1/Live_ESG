<template>
  <div class="example-container">
    <h1 class="example-title">Score Visualization Component Examples</h1>

    <!-- Example 1: Single Score Display -->
    <section class="example-section">
      <h2 class="example-subtitle">Example 1: Current Score Display</h2>
      <p class="example-description">
        Display a single ESG score with pillar breakdown. No trend data shown.
      </p>
      <ScoreVisualization :score="singleScore" :show-trend="false" />
    </section>

    <!-- Example 2: Score with Trend -->
    <section class="example-section">
      <h2 class="example-subtitle">Example 2: Score with Multi-Year Trend</h2>
      <p class="example-description">
        Display current score along with historical trend data showing improvement over time.
      </p>
      <ScoreVisualization :score="currentScore" :score-history="scoreHistory" :show-trend="true" />
    </section>

    <!-- Example 3: Low Score -->
    <section class="example-section">
      <h2 class="example-subtitle">Example 3: Low Score Display</h2>
      <p class="example-description">
        Display a company with lower ESG scores to show different color coding.
      </p>
      <ScoreVisualization :score="lowScore" :show-trend="false" />
    </section>

    <!-- Example 4: Loading State -->
    <section class="example-section">
      <h2 class="example-subtitle">Example 4: Loading State</h2>
      <p class="example-description">
        When score data is not yet available (null).
      </p>
      <ScoreVisualization :score="null" :show-trend="false" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScoreVisualization from './ScoreVisualization.vue'
import type { ESGScore } from '@/types'

// Example 1: Single score
const singleScore = ref<ESGScore>({
  id: 1,
  company_id: 1,
  report_year: 2024,
  environmental_score: 78.5,
  social_score: 82.3,
  governance_score: 75.8,
  overall_score: 78.9,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {}
  },
  calculated_at: '2024-01-15T10:30:00Z'
})

// Example 2: Current score with history
const currentScore = ref<ESGScore>({
  id: 5,
  company_id: 2,
  report_year: 2024,
  environmental_score: 85.2,
  social_score: 88.7,
  governance_score: 82.4,
  overall_score: 85.4,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {}
  },
  calculated_at: '2024-01-15T10:30:00Z'
})

const scoreHistory = ref<ESGScore[]>([
  {
    id: 2,
    company_id: 2,
    report_year: 2021,
    environmental_score: 72.5,
    social_score: 75.3,
    governance_score: 70.8,
    overall_score: 72.9,
    calculation_metadata: {
      weights: {
        environmental: 0.33,
        social: 0.33,
        governance: 0.34
      },
      indicators: {}
    },
    calculated_at: '2021-12-15T10:30:00Z'
  },
  {
    id: 3,
    company_id: 2,
    report_year: 2022,
    environmental_score: 76.8,
    social_score: 80.1,
    governance_score: 75.2,
    overall_score: 77.4,
    calculation_metadata: {
      weights: {
        environmental: 0.33,
        social: 0.33,
        governance: 0.34
      },
      indicators: {}
    },
    calculated_at: '2022-12-15T10:30:00Z'
  },
  {
    id: 4,
    company_id: 2,
    report_year: 2023,
    environmental_score: 81.3,
    social_score: 84.5,
    governance_score: 79.6,
    overall_score: 81.8,
    calculation_metadata: {
      weights: {
        environmental: 0.33,
        social: 0.33,
        governance: 0.34
      },
      indicators: {}
    },
    calculated_at: '2023-12-15T10:30:00Z'
  },
  {
    id: 5,
    company_id: 2,
    report_year: 2024,
    environmental_score: 85.2,
    social_score: 88.7,
    governance_score: 82.4,
    overall_score: 85.4,
    calculation_metadata: {
      weights: {
        environmental: 0.33,
        social: 0.33,
        governance: 0.34
      },
      indicators: {}
    },
    calculated_at: '2024-01-15T10:30:00Z'
  }
])

// Example 3: Low score
const lowScore = ref<ESGScore>({
  id: 6,
  company_id: 3,
  report_year: 2024,
  environmental_score: 42.5,
  social_score: 38.3,
  governance_score: 45.8,
  overall_score: 42.2,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {}
  },
  calculated_at: '2024-01-15T10:30:00Z'
})
</script>

<style scoped>
.example-container {
  @apply max-w-7xl mx-auto p-8 space-y-12;
}

.example-title {
  @apply text-4xl font-bold text-gray-900 mb-8;
}

.example-section {
  @apply space-y-4;
}

.example-subtitle {
  @apply text-2xl font-semibold text-gray-800;
}

.example-description {
  @apply text-gray-600 mb-6;
}
</style>
