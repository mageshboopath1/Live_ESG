<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p class="text-gray-600">Loading company data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
      <div class="flex items-start">
        <svg class="w-6 h-6 text-red-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <h3 class="text-red-800 font-semibold mb-1">Error Loading Company</h3>
          <p class="text-red-700">{{ error }}</p>
          <button @click="retryLoad" class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition">
            Retry
          </button>
        </div>
      </div>
    </div>

    <!-- Company Dashboard -->
    <div v-else-if="company">
      <!-- Company Header -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h1 class="text-3xl font-bold text-gray-900">{{ company.company_name }}</h1>
              <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                {{ company.symbol }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-gray-600">
              <div class="flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span class="font-medium">{{ company.industry || 'N/A' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span class="text-sm">ISIN: {{ company.isin_code }}</span>
              </div>
            </div>
          </div>
          <button @click="refreshData" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      <!-- Available Reports Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Available Reports
        </h2>

        <div v-if="reportsLoading" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p class="text-gray-600 text-sm">Loading reports...</p>
        </div>

        <div v-else-if="reports.length === 0" class="text-center py-8 text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No reports available for this company</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="report in sortedReports"
            :key="report.id"
            class="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
            :class="getReportBorderClass(report.status)"
            @click="selectReport(report)"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="flex-1">
                <h3 class="font-semibold text-gray-900">{{ report.report_year }}</h3>
                <p class="text-sm text-gray-600">{{ report.report_type || 'Report' }}</p>
              </div>
              <span
                class="px-2 py-1 text-xs font-medium rounded"
                :class="getStatusClass(report.status)"
              >
                {{ report.status }}
              </span>
            </div>
            <div class="text-xs text-gray-500 mt-2">
              <p>Ingested: {{ formatDate(report.ingested_at) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Year Selector for Indicators -->
      <div v-if="availableYears.length > 0" class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            BRSR Core Indicators
          </h2>
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium text-gray-700">Report Year:</label>
            <select
              v-model="selectedYear"
              @change="loadIndicators"
              class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option v-for="year in availableYears" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Indicators by BRSR Attributes -->
      <div v-if="selectedYear && !indicatorsLoading">
        <div v-if="Object.keys(indicatorsByAttribute).length === 0" class="bg-white rounded-lg shadow-md p-8 text-center">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-gray-600 text-lg">No indicators extracted for {{ selectedYear }}</p>
          <p class="text-gray-500 text-sm mt-2">The report may still be processing or no data is available.</p>
        </div>

        <div v-else class="space-y-6">
          <div
            v-for="(indicators, attrNum) in indicatorsByAttribute"
            :key="attrNum"
            class="bg-white rounded-lg shadow-md overflow-hidden"
          >
            <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
              <h3 class="text-lg font-semibold text-white flex items-center gap-2">
                <span class="bg-white text-blue-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                  {{ attrNum }}
                </span>
                {{ getAttributeName(attrNum) }}
                <span class="ml-auto text-sm font-normal bg-blue-500 px-3 py-1 rounded-full">
                  {{ indicators.length }} indicator{{ indicators.length !== 1 ? 's' : '' }}
                </span>
              </h3>
            </div>

            <div class="p-6">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div
                  v-for="indicator in indicators"
                  :key="indicator.id"
                  class="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  :class="getIndicatorBorderClass(indicator.validation_status)"
                  @click="viewIndicatorDetails(indicator)"
                >
                  <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                      <h4 class="font-semibold text-gray-900 mb-1">
                        {{ getIndicatorDefinition(indicator.indicator_id)?.parameter_name || 'Unknown Indicator' }}
                      </h4>
                      <p class="text-xs text-gray-500">
                        {{ getIndicatorDefinition(indicator.indicator_id)?.indicator_code || '' }}
                      </p>
                    </div>
                    <span
                      class="px-2 py-1 text-xs font-medium rounded flex-shrink-0"
                      :class="getPillarClass(getIndicatorDefinition(indicator.indicator_id)?.pillar)"
                    >
                      {{ getIndicatorDefinition(indicator.indicator_id)?.pillar || 'N/A' }}
                    </span>
                  </div>

                  <div class="mb-3">
                    <div class="flex items-baseline gap-2">
                      <span class="text-2xl font-bold text-gray-900">
                        {{ formatIndicatorValue(indicator) }}
                      </span>
                      <span class="text-sm text-gray-600">
                        {{ getIndicatorDefinition(indicator.indicator_id)?.measurement_unit || '' }}
                      </span>
                    </div>
                  </div>

                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <div class="flex items-center gap-1">
                        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span class="text-xs text-gray-600">
                          Confidence: {{ (indicator.confidence_score * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <div
                        class="w-16 h-2 bg-gray-200 rounded-full overflow-hidden"
                        :title="`Confidence: ${(indicator.confidence_score * 100).toFixed(0)}%`"
                      >
                        <div
                          class="h-full rounded-full transition-all"
                          :class="getConfidenceBarClass(indicator.confidence_score)"
                          :style="{ width: `${indicator.confidence_score * 100}%` }"
                        ></div>
                      </div>
                    </div>
                    <span
                      class="px-2 py-1 text-xs font-medium rounded"
                      :class="getValidationClass(indicator.validation_status)"
                    >
                      {{ indicator.validation_status }}
                    </span>
                  </div>

                  <div v-if="indicator.source_pages && indicator.source_pages.length > 0" class="mt-3 pt-3 border-t">
                    <div class="flex items-center gap-2 text-xs text-gray-600">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <span>Source: Pages {{ indicator.source_pages.join(', ') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Indicators Loading State -->
      <div v-else-if="indicatorsLoading" class="bg-white rounded-lg shadow-md p-8 text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p class="text-gray-600">Loading indicators...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import { useIndicatorStore } from '@/stores/indicatorStore'
import type { Report, ExtractedIndicator } from '@/types'

const route = useRoute()
const companyStore = useCompanyStore()
const indicatorStore = useIndicatorStore()

// State
const loading = ref(true)
const reportsLoading = ref(false)
const indicatorsLoading = ref(false)
const error = ref<string | null>(null)
const selectedYear = ref<number | null>(null)

// Computed
const company = computed(() => companyStore.selectedCompany)
const reports = computed(() => companyStore.reports)
const definitions = computed(() => indicatorStore.definitions)

const sortedReports = computed(() => {
  return [...reports.value].sort((a, b) => b.report_year - a.report_year)
})

const availableYears = computed(() => {
  const years = reports.value
    .filter(r => r.status === 'SUCCESS')
    .map(r => r.report_year)
  return [...new Set(years)].sort((a, b) => b - a)
})

const indicatorsByAttribute = computed(() => {
  return indicatorStore.indicatorsByAttribute
})

// BRSR Attribute Names
const attributeNames: Record<number, string> = {
  1: 'GHG Footprint (Scope 1 & 2)',
  2: 'Water Footprint',
  3: 'Energy Footprint',
  4: 'Waste Management',
  5: 'Employee Well-being',
  6: 'Gender Diversity',
  7: 'Inclusive Development',
  8: 'Customer Fairness',
  9: 'Business Openness'
}

// Methods
const loadCompanyData = async () => {
  const companyId = parseInt(route.params.id as string)
  
  if (isNaN(companyId)) {
    error.value = 'Invalid company ID'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = null

    // Load company details
    await companyStore.fetchCompanyById(companyId)

    // Load indicator definitions if not already loaded
    if (definitions.value.length === 0) {
      await indicatorStore.fetchDefinitions()
    }

    // Load reports
    reportsLoading.value = true
    await companyStore.fetchCompanyReports(companyId)
    reportsLoading.value = false

    // Auto-select most recent year if available
    if (availableYears.value.length > 0 && !selectedYear.value) {
      selectedYear.value = availableYears.value[0]
      await loadIndicators()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load company data'
    console.error('Error loading company data:', err)
  } finally {
    loading.value = false
  }
}

const loadIndicators = async () => {
  if (!company.value || !selectedYear.value) return

  try {
    indicatorsLoading.value = true
    await indicatorStore.fetchCompanyIndicators(company.value.id, selectedYear.value)
  } catch (err) {
    console.error('Error loading indicators:', err)
  } finally {
    indicatorsLoading.value = false
  }
}

const refreshData = async () => {
  if (!company.value) return
  
  try {
    loading.value = true
    await companyStore.fetchCompanyById(company.value.id, true)
    await companyStore.fetchCompanyReports(company.value.id, true)
    
    if (selectedYear.value) {
      await indicatorStore.fetchCompanyIndicators(company.value.id, selectedYear.value, undefined, true)
    }
  } catch (err) {
    console.error('Error refreshing data:', err)
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loadCompanyData()
}

const selectReport = (report: Report) => {
  console.log('Selected report:', report)
  // Future: Navigate to report details or trigger processing
}

const viewIndicatorDetails = (indicator: ExtractedIndicator) => {
  console.log('View indicator details:', indicator)
  // Future: Open modal or navigate to indicator details page
}

const getAttributeName = (attrNum: number): string => {
  return attributeNames[attrNum] || `Attribute ${attrNum}`
}

const getIndicatorDefinition = (indicatorId: number) => {
  return indicatorStore.getDefinitionById(indicatorId)
}

const formatIndicatorValue = (indicator: ExtractedIndicator): string => {
  if (indicator.numeric_value !== null && indicator.numeric_value !== undefined) {
    return indicator.numeric_value.toLocaleString()
  }
  return indicator.extracted_value || 'N/A'
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

// Styling helpers
const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    SUCCESS: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
    PENDING: 'bg-yellow-100 text-yellow-800',
    PROCESSING: 'bg-blue-100 text-blue-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getReportBorderClass = (status: string): string => {
  const classes: Record<string, string> = {
    SUCCESS: 'border-green-200',
    FAILED: 'border-red-200',
    PENDING: 'border-yellow-200',
    PROCESSING: 'border-blue-200'
  }
  return classes[status] || 'border-gray-200'
}

const getValidationClass = (status: string): string => {
  const classes: Record<string, string> = {
    valid: 'bg-green-100 text-green-800',
    invalid: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getIndicatorBorderClass = (status: string): string => {
  const classes: Record<string, string> = {
    valid: 'border-green-200',
    invalid: 'border-red-200',
    pending: 'border-yellow-200'
  }
  return classes[status] || 'border-gray-200'
}

const getPillarClass = (pillar?: 'E' | 'S' | 'G'): string => {
  const classes: Record<string, string> = {
    E: 'bg-green-100 text-green-800',
    S: 'bg-blue-100 text-blue-800',
    G: 'bg-purple-100 text-purple-800'
  }
  return classes[pillar || ''] || 'bg-gray-100 text-gray-800'
}

const getConfidenceBarClass = (confidence: number): string => {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.6) return 'bg-yellow-500'
  return 'bg-red-500'
}

// Lifecycle
onMounted(() => {
  loadCompanyData()
})

// Watch for route changes
watch(() => route.params.id, () => {
  if (route.name === 'company') {
    loadCompanyData()
  }
})
</script>

<style scoped>
/* Add any component-specific styles here */
</style>
