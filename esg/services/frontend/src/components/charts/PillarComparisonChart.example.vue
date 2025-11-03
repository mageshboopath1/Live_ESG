<template>
  <div class="example-container">
    <h1 class="example-title">Pillar Comparison Chart Examples</h1>

    <section class="example-section">
      <h2 class="section-title">Single Company Pillar Scores</h2>
      <p class="section-description">
        Radar chart showing Environmental, Social, and Governance scores for a single company.
      </p>
      <div class="chart-wrapper">
        <PillarComparisonChart
          :scores="[singleCompanyScore]"
          :company-names="['Reliance Industries']"
          @pillar-click="handlePillarClick"
        />
      </div>
    </section>

    <section class="example-section">
      <h2 class="section-title">Multi-Company Comparison</h2>
      <p class="section-description">
        Compare ESG pillar scores across multiple companies.
      </p>
      <div class="chart-wrapper">
        <PillarComparisonChart
          :scores="multiCompanyScores"
          :company-names="['Reliance Industries', 'Tata Consultancy Services', 'Infosys']"
          :show-breakdown="false"
          @pillar-click="handlePillarClick"
        />
      </div>
    </section>

    <section class="example-section">
      <h2 class="section-title">With Breakdown Panel</h2>
      <p class="section-description">
        Shows detailed breakdown with source indicators for each pillar.
      </p>
      <div class="chart-wrapper">
        <PillarComparisonChart
          :scores="[detailedScore]"
          :company-names="['HDFC Bank']"
          :show-breakdown="true"
          @pillar-click="handlePillarClick"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import PillarComparisonChart from './PillarComparisonChart.vue'
import type { ESGScore } from '@/types'

const singleCompanyScore: ESGScore = {
  id: 1,
  company_id: 1,
  report_year: 2023,
  environmental_score: 78.5,
  social_score: 82.3,
  governance_score: 85.1,
  overall_score: 81.9,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {
      'GHG_SCOPE1': { value: 1100, weight: 0.3, pillar: 'E' },
      'WATER_CONSUMPTION': { value: 46000, weight: 0.25, pillar: 'E' },
      'ENERGY_CONSUMPTION': { value: 85000, weight: 0.25, pillar: 'E' },
      'EMPLOYEE_WELLBEING': { value: 92, weight: 0.4, pillar: 'S' },
      'GENDER_DIVERSITY': { value: 35, weight: 0.3, pillar: 'S' },
      'BOARD_INDEPENDENCE': { value: 65, weight: 0.5, pillar: 'G' }
    }
  },
  calculated_at: '2024-01-15T10:00:00Z'
}

const multiCompanyScores: ESGScore[] = [
  {
    id: 1,
    company_id: 1,
    report_year: 2023,
    environmental_score: 78.5,
    social_score: 82.3,
    governance_score: 85.1,
    overall_score: 81.9,
    calculation_metadata: {
      weights: { environmental: 0.33, social: 0.33, governance: 0.34 },
      indicators: {}
    },
    calculated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 2,
    company_id: 2,
    report_year: 2023,
    environmental_score: 72.1,
    social_score: 88.5,
    governance_score: 91.2,
    overall_score: 83.9,
    calculation_metadata: {
      weights: { environmental: 0.33, social: 0.33, governance: 0.34 },
      indicators: {}
    },
    calculated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 3,
    company_id: 3,
    report_year: 2023,
    environmental_score: 75.8,
    social_score: 90.2,
    governance_score: 89.5,
    overall_score: 85.2,
    calculation_metadata: {
      weights: { environmental: 0.33, social: 0.33, governance: 0.34 },
      indicators: {}
    },
    calculated_at: '2024-01-15T10:00:00Z'
  }
]

const detailedScore: ESGScore = {
  id: 4,
  company_id: 4,
  report_year: 2023,
  environmental_score: 68.5,
  social_score: 85.7,
  governance_score: 92.3,
  overall_score: 82.2,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {
      'GHG_SCOPE1': { value: 850, weight: 0.3, pillar: 'E' },
      'GHG_SCOPE2': { value: 1200, weight: 0.25, pillar: 'E' },
      'WATER_CONSUMPTION': { value: 32000, weight: 0.2, pillar: 'E' },
      'WASTE_RECYCLED': { value: 65, weight: 0.15, pillar: 'E' },
      'EMPLOYEE_WELLBEING': { value: 88, weight: 0.35, pillar: 'S' },
      'GENDER_DIVERSITY': { value: 42, weight: 0.25, pillar: 'S' },
      'TRAINING_HOURS': { value: 45, weight: 0.2, pillar: 'S' },
      'COMMUNITY_INVESTMENT': { value: 2.5, weight: 0.2, pillar: 'S' },
      'BOARD_INDEPENDENCE': { value: 75, weight: 0.4, pillar: 'G' },
      'ETHICS_TRAINING': { value: 95, weight: 0.3, pillar: 'G' },
      'AUDIT_COMMITTEE': { value: 100, weight: 0.3, pillar: 'G' }
    }
  },
  calculated_at: '2024-01-15T10:00:00Z'
}

const handlePillarClick = (pillar: 'E' | 'S' | 'G') => {
  console.log('Pillar clicked:', pillar)
  alert(`Showing detailed breakdown for ${pillar} pillar`)
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
