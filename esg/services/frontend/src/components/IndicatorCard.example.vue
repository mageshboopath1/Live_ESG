<template>
  <div class="example-container">
    <h2 class="text-2xl font-bold mb-6">IndicatorCard Component Examples</h2>

    <!-- Example 1: High Confidence, Valid Indicator -->
    <div class="example-section">
      <h3 class="text-lg font-semibold mb-3">Example 1: High Confidence Environmental Indicator</h3>
      <IndicatorCard
        :indicator="exampleIndicator1"
        pdf-name="RELIANCE/2024_BRSR.pdf"
        :source-pages="[45, 46]"
        @citation-click="handleCitationClick"
      />
    </div>

    <!-- Example 2: Medium Confidence, Pending Validation -->
    <div class="example-section">
      <h3 class="text-lg font-semibold mb-3">Example 2: Medium Confidence Social Indicator</h3>
      <IndicatorCard
        :indicator="exampleIndicator2"
        pdf-name="TCS/2023_Annual_Report.pdf"
        :source-pages="[78]"
        @citation-click="handleCitationClick"
      />
    </div>

    <!-- Example 3: Low Confidence, Invalid -->
    <div class="example-section">
      <h3 class="text-lg font-semibold mb-3">Example 3: Low Confidence Governance Indicator</h3>
      <IndicatorCard
        :indicator="exampleIndicator3"
        pdf-name="INFY/2024_BRSR.pdf"
        :source-pages="[12, 13, 14, 15]"
        @citation-click="handleCitationClick"
      />
    </div>

    <!-- Example 4: Without Citation -->
    <div class="example-section">
      <h3 class="text-lg font-semibold mb-3">Example 4: Indicator Without Citation</h3>
      <IndicatorCard
        :indicator="exampleIndicator1"
        :show-citation="false"
      />
    </div>

    <!-- Grid Layout Example -->
    <div class="example-section">
      <h3 class="text-lg font-semibold mb-3">Example 5: Grid Layout (Typical Dashboard View)</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <IndicatorCard
          v-for="indicator in gridIndicators"
          :key="indicator.id"
          :indicator="indicator"
          pdf-name="RELIANCE/2024_BRSR.pdf"
          :source-pages="[45]"
          @citation-click="handleCitationClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import IndicatorCard from './IndicatorCard.vue'
import type { Indicator } from '@/types'

// Example indicators
const exampleIndicator1: Indicator = {
  id: 1,
  code: 'GHG_SCOPE1',
  name: 'Total Scope 1 emissions',
  value: '1250',
  numericValue: 1250,
  unit: 'MT CO2e',
  confidence: 0.95,
  validationStatus: 'valid',
  attributeNumber: 1,
  pillar: 'E'
}

const exampleIndicator2: Indicator = {
  id: 2,
  code: 'EMP_TURNOVER',
  name: 'Employee turnover rate',
  value: '12.5',
  numericValue: 12.5,
  unit: '%',
  confidence: 0.72,
  validationStatus: 'pending',
  attributeNumber: 5,
  pillar: 'S'
}

const exampleIndicator3: Indicator = {
  id: 3,
  code: 'BOARD_DIVERSITY',
  name: 'Board diversity percentage',
  value: '35',
  numericValue: 35,
  unit: '%',
  confidence: 0.45,
  validationStatus: 'invalid',
  attributeNumber: 6,
  pillar: 'G'
}

const gridIndicators: Indicator[] = [
  {
    id: 4,
    code: 'WATER_CONSUMPTION',
    name: 'Total water consumption',
    value: '45000',
    numericValue: 45000,
    unit: 'KL',
    confidence: 0.88,
    validationStatus: 'valid',
    attributeNumber: 2,
    pillar: 'E'
  },
  {
    id: 5,
    code: 'ENERGY_CONSUMPTION',
    name: 'Total energy consumption',
    value: '125000',
    numericValue: 125000,
    unit: 'GJ',
    confidence: 0.91,
    validationStatus: 'valid',
    attributeNumber: 3,
    pillar: 'E'
  },
  {
    id: 6,
    code: 'WASTE_GENERATED',
    name: 'Total waste generated',
    value: '8500',
    numericValue: 8500,
    unit: 'MT',
    confidence: 0.85,
    validationStatus: 'valid',
    attributeNumber: 4,
    pillar: 'E'
  }
]

// Event handler
const handleCitationClick = (indicator: Indicator) => {
  console.log('Citation clicked for indicator:', indicator)
  alert(`Opening citation viewer for: ${indicator.name}`)
  // In a real application, this would open a modal or navigate to citation viewer
}
</script>

<style scoped>
.example-container {
  @apply max-w-7xl mx-auto p-6;
}

.example-section {
  @apply mb-8 p-6 bg-gray-50 rounded-lg;
}
</style>
