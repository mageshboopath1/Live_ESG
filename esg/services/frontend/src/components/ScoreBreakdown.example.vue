<template>
  <div class="example-container">
    <h1 class="example-title">Score Breakdown Component Example</h1>
    
    <!-- Example 1: With Full Data -->
    <section class="example-section">
      <h2 class="section-title">Example 1: Complete Score Breakdown</h2>
      <ScoreBreakdown
        :breakdown="mockBreakdown"
        :overall-score="mockOverallScore"
        @indicator-click="handleIndicatorClick"
      />
    </section>

    <!-- Example 2: Loading State -->
    <section class="example-section">
      <h2 class="section-title">Example 2: Loading State</h2>
      <ScoreBreakdown
        :breakdown="null"
        :loading="true"
      />
    </section>

    <!-- Example 3: Error State -->
    <section class="example-section">
      <h2 class="section-title">Example 3: Error State</h2>
      <ScoreBreakdown
        :breakdown="null"
        :error="'Failed to load score breakdown. Please try again.'"
      />
    </section>

    <!-- Example 4: Empty State -->
    <section class="example-section">
      <h2 class="section-title">Example 4: Empty State</h2>
      <ScoreBreakdown :breakdown="null" />
    </section>

    <!-- Indicator Click Handler Demo -->
    <div v-if="selectedIndicator" class="indicator-modal">
      <div class="modal-content">
        <h3 class="modal-title">Indicator Details</h3>
        <p class="modal-text">Code: {{ selectedIndicator.code }}</p>
        <p class="modal-text">Value: {{ selectedIndicator.value }}</p>
        <p class="modal-text">Weight: {{ (selectedIndicator.weight * 100).toFixed(0) }}%</p>
        <button class="modal-close" @click="selectedIndicator = null">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScoreBreakdown from './ScoreBreakdown.vue'
import type { ScoreBreakdown as ScoreBreakdownType, IndicatorContribution } from '@/types'

// Mock data
const mockOverallScore = 72.5

const mockBreakdown: ScoreBreakdownType = {
  pillars: [
    {
      name: 'Environmental',
      score: 75.2,
      weight: 0.33,
      indicators: [
        {
          code: 'GHG_SCOPE1',
          value: 1250.5,
          weight: 0.25,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [45, 46],
              chunkText: 'Our total Scope 1 emissions for FY 2024 were 1,250.5 MT CO2e...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/45'
            }
          ]
        },
        {
          code: 'GHG_SCOPE2',
          value: 3420.8,
          weight: 0.25,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [46],
              chunkText: 'Scope 2 emissions totaled 3,420.8 MT CO2e...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/46'
            }
          ]
        },
        {
          code: 'WATER_CONSUMPTION',
          value: 125000,
          weight: 0.20,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [52, 53],
              chunkText: 'Total water consumption was 125,000 kiloliters...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/52'
            }
          ]
        },
        {
          code: 'ENERGY_CONSUMPTION',
          value: 450000,
          weight: 0.20,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [48, 49, 50],
              chunkText: 'Energy consumption reached 450,000 GJ...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/48'
            }
          ]
        },
        {
          code: 'WASTE_RECYCLED',
          value: 85.5,
          weight: 0.10,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [55],
              chunkText: 'We recycled 85.5% of our waste...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/55'
            }
          ]
        }
      ]
    },
    {
      name: 'Social',
      score: 68.9,
      weight: 0.33,
      indicators: [
        {
          code: 'EMPLOYEE_TURNOVER',
          value: 12.3,
          weight: 0.20,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [62],
              chunkText: 'Employee turnover rate was 12.3%...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/62'
            }
          ]
        },
        {
          code: 'GENDER_DIVERSITY',
          value: 28.5,
          weight: 0.25,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [64, 65],
              chunkText: 'Women comprise 28.5% of our workforce...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/64'
            }
          ]
        },
        {
          code: 'TRAINING_HOURS',
          value: 42.5,
          weight: 0.15,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [68],
              chunkText: 'Average training hours per employee: 42.5...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/68'
            }
          ]
        },
        {
          code: 'SAFETY_INCIDENTS',
          value: 2.1,
          weight: 0.25,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [70, 71],
              chunkText: 'Lost time injury frequency rate: 2.1...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/70'
            }
          ]
        },
        {
          code: 'COMMUNITY_INVESTMENT',
          value: 15000000,
          weight: 0.15,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [75],
              chunkText: 'Community investment totaled ₹15 crore...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/75'
            }
          ]
        }
      ]
    },
    {
      name: 'Governance',
      score: 73.4,
      weight: 0.34,
      indicators: [
        {
          code: 'BOARD_INDEPENDENCE',
          value: 60.0,
          weight: 0.30,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [82],
              chunkText: 'Independent directors comprise 60% of the board...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/82'
            }
          ]
        },
        {
          code: 'BOARD_DIVERSITY',
          value: 33.3,
          weight: 0.20,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [83],
              chunkText: 'Women directors represent 33.3% of the board...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/83'
            }
          ]
        },
        {
          code: 'ETHICS_TRAINING',
          value: 95.0,
          weight: 0.20,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [88, 89],
              chunkText: '95% of employees completed ethics training...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/88'
            }
          ]
        },
        {
          code: 'WHISTLEBLOWER_CASES',
          value: 8,
          weight: 0.15,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [92],
              chunkText: 'Eight whistleblower cases were reported and resolved...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/92'
            }
          ]
        },
        {
          code: 'AUDIT_COMMITTEE_MEETINGS',
          value: 6,
          weight: 0.15,
          citations: [
            {
              pdfName: 'RELIANCE/2024_BRSR.pdf',
              pages: [85],
              chunkText: 'The audit committee met 6 times during the year...',
              url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/85'
            }
          ]
        }
      ]
    }
  ]
}

// State
const selectedIndicator = ref<IndicatorContribution | null>(null)

// Methods
const handleIndicatorClick = (indicator: IndicatorContribution) => {
  selectedIndicator.value = indicator
  console.log('Indicator clicked:', indicator)
}
</script>

<style scoped>
.example-container {
  @apply max-w-7xl mx-auto p-6 space-y-8;
}

.example-title {
  @apply text-3xl font-bold text-gray-900 mb-8;
}

.example-section {
  @apply space-y-4;
}

.section-title {
  @apply text-xl font-semibold text-gray-800 mb-4;
}

/* Modal */
.indicator-modal {
  @apply fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50;
}

.modal-content {
  @apply bg-white rounded-lg p-6 max-w-md w-full mx-4 space-y-4;
}

.modal-title {
  @apply text-xl font-bold text-gray-900;
}

.modal-text {
  @apply text-sm text-gray-700;
}

.modal-close {
  @apply w-full px-4 py-2 bg-blue-600 text-white rounded-lg;
  @apply hover:bg-blue-700 transition-colors;
}
</style>
