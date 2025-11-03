<template>
  <div class="container mx-auto px-4 py-8">
    <div class="max-w-6xl mx-auto">
      <div class="text-center mb-12">
        <h1 class="text-4xl font-bold text-gray-900 mb-4">
          ESG Intelligence Platform
        </h1>
        <p class="text-lg text-gray-600 mb-8">
          Transparent ESG analysis with AI-powered indicator extraction and source citations
        </p>
      </div>

      <!-- Company Search Component -->
      <div class="mb-12">
        <h2 class="text-2xl font-semibold text-gray-900 mb-6">Search Companies</h2>
        <CompanySearch @select="handleCompanySelect" />
      </div>
      
      <!-- Feature Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="card">
          <h3 class="text-xl font-semibold mb-2">Companies</h3>
          <p class="text-gray-600">Browse NIFTY 50 companies and their ESG reports</p>
        </div>
        
        <div class="card">
          <h3 class="text-xl font-semibold mb-2">Indicators</h3>
          <p class="text-gray-600">View extracted BRSR Core indicators with citations</p>
        </div>
        
        <div class="card">
          <h3 class="text-xl font-semibold mb-2">Scores</h3>
          <p class="text-gray-600">Analyze ESG scores with transparent derivation</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CompanySearch from '@/components/CompanySearch.vue'
import type { Company } from '@/types'

const handleCompanySelect = (company: Company) => {
  console.log('Selected company:', company)
  // Navigation is handled by the CompanySearch component
}
</script>
