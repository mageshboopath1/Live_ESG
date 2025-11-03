<template>
  <div class="score-view">
    <div class="view-header">
      <h1 class="view-title">ESG Score Analysis</h1>
      <p v-if="company" class="view-subtitle">
        {{ company.company_name }} - {{ selectedYear }}
      </p>
    </div>

    <!-- Score Visualization -->
    <section class="score-section">
      <ScoreVisualization
        :score="scoreStore.selectedScore"
        :score-history="scoreStore.scoreHistory"
        :show-trend="true"
      />
    </section>

    <!-- Score Breakdown -->
    <section class="breakdown-section">
      <div class="section-header">
        <h2 class="section-title">Transparent Score Breakdown</h2>
        <p class="section-description">
          See exactly how the ESG score is calculated from individual indicators with full source citations.
        </p>
      </div>
      
      <ScoreBreakdown
        :breakdown="scoreStore.scoreBreakdown"
        :overall-score="scoreStore.selectedScore?.overall_score || 0"
        :loading="scoreStore.loading"
        :error="scoreStore.error"
        @indicator-click="handleIndicatorClick"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useScoreStore } from '@/stores/scoreStore'
import { useCompanyStore } from '@/stores/companyStore'
import ScoreVisualization from '@/components/ScoreVisualization.vue'
import ScoreBreakdown from '@/components/ScoreBreakdown.vue'
import type { IndicatorContribution } from '@/types'

const route = useRoute()
const scoreStore = useScoreStore()
const companyStore = useCompanyStore()

// Get company ID and year from route params
const companyId = computed(() => parseInt(route.params.companyId as string))
const selectedYear = computed(() => parseInt(route.params.year as string) || new Date().getFullYear())

// Get company data
const company = computed(() => companyStore.companies.find(c => c.id === companyId.value))

// Load data on mount
onMounted(async () => {
  try {
    // Fetch company if not already loaded
    if (!company.value) {
      await companyStore.fetchCompanyById(companyId.value)
    }

    // Fetch score and breakdown
    await Promise.all([
      scoreStore.fetchCompanyScore(companyId.value, selectedYear.value),
      scoreStore.fetchScoreBreakdown(companyId.value, selectedYear.value),
      scoreStore.fetchScoreHistory(companyId.value)
    ])
  } catch (error) {
    console.error('Failed to load score data:', error)
  }
})

// Handle indicator click
const handleIndicatorClick = (indicator: IndicatorContribution) => {
  console.log('Indicator clicked:', indicator)
  
  // Navigate to indicator detail or open citation viewer
  // For now, we'll just log it
  // TODO: Implement navigation to citation viewer or indicator detail page
  
  // Example navigation:
  // router.push({
  //   name: 'citation-viewer',
  //   params: { indicatorCode: indicator.code },
  //   query: { companyId: companyId.value, year: selectedYear.value }
  // })
}
</script>

<style scoped>
.score-view {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8;
}

/* Header */
.view-header {
  @apply mb-8;
}

.view-title {
  @apply text-3xl font-bold text-gray-900 mb-2;
}

.view-subtitle {
  @apply text-lg text-gray-600;
}

/* Sections */
.score-section,
.breakdown-section {
  @apply space-y-6;
}

.section-header {
  @apply mb-6;
}

.section-title {
  @apply text-2xl font-bold text-gray-900 mb-2;
}

.section-description {
  @apply text-gray-600;
}
</style>
