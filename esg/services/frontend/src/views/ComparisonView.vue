<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Company Comparison</h1>
      <p class="text-gray-600">Compare ESG indicators across multiple companies side-by-side</p>
    </div>

    <!-- Company Selection -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        Select Companies (2-4)
      </h2>

      <!-- Company Search -->
      <div class="mb-4">
        <div class="relative">
          <input
            v-model="searchQuery"
            @input="handleSearch"
            type="text"
            placeholder="Search companies by name or symbol..."
            class="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <svg class="absolute left-3 top-3.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <!-- Search Results Dropdown -->
        <div v-if="searchResults.length > 0 && searchQuery" class="mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          <button
            v-for="company in searchResults"
            :key="company.id"
            @click="addCompany(company)"
            :disabled="isCompanySelected(company.id) || selectedCompanies.length >= 4"
            class="w-full px-4 py-3 text-left hover:bg-gray-50 border-b last:border-b-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="font-semibold text-gray-900">{{ company.company_name }}</p>
                <p class="text-sm text-gray-600">{{ company.symbol }} • {{ company.industry }}</p>
              </div>
              <span v-if="isCompanySelected(company.id)" class="text-green-600 text-sm">✓ Selected</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Selected Companies -->
      <div v-if="selectedCompanies.length > 0" class="space-y-2">
        <p class="text-sm font-medium text-gray-700 mb-2">Selected Companies ({{ selectedCompanies.length }}/4):</p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="company in selectedCompanies"
            :key="company.id"
            class="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <span class="font-medium text-gray-900">{{ company.company_name }}</span>
            <span class="text-sm text-gray-600">({{ company.symbol }})</span>
            <button
              @click="removeCompany(company.id)"
              class="ml-2 text-red-600 hover:text-red-800"
              title="Remove"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Year Selection -->
      <div v-if="selectedCompanies.length >= 2" class="mt-4 flex items-center gap-4">
        <label class="text-sm font-medium text-gray-700">Report Year:</label>
        <select
          v-model="selectedYear"
          @change="loadComparison"
          class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select Year</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>

        <button
          @click="loadComparison"
          :disabled="!selectedYear || loading"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Compare
        </button>

        <button
          v-if="comparisonData"
          @click="exportData"
          class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-lg shadow-md p-12 text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600">Loading comparison data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex items-start">
        <svg class="w-6 h-6 text-red-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <h3 class="text-red-800 font-semibold mb-1">Error Loading Comparison</h3>
          <p class="text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Comparison Table -->
    <div v-else-if="comparisonData && selectedCompanies.length >= 2" class="space-y-6">
      <!-- Filter Controls -->
      <div class="bg-white rounded-lg shadow-md p-4">
        <div class="flex items-center gap-4 flex-wrap">
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">Filter by Pillar:</label>
            <select
              v-model="filterPillar"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Pillars</option>
              <option value="E">Environmental</option>
              <option value="S">Social</option>
              <option value="G">Governance</option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">Filter by Attribute:</label>
            <select
              v-model="filterAttribute"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Attributes</option>
              <option v-for="attr in 9" :key="attr" :value="attr">
                {{ attr }}. {{ getAttributeName(attr) }}
              </option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <input
              v-model="highlightDifferences"
              type="checkbox"
              id="highlight-diff"
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label for="highlight-diff" class="text-sm font-medium text-gray-700">
              Highlight Significant Differences
            </label>
          </div>
        </div>
      </div>

      <!-- Comparison Table by Attribute -->
      <div
        v-for="(indicators, attrNum) in groupedIndicators"
        :key="attrNum"
        class="bg-white rounded-lg shadow-md overflow-hidden"
      >
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <h3 class="text-lg font-semibold text-white flex items-center gap-2">
            <span class="bg-white text-blue-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
              {{ attrNum }}
            </span>
            {{ getAttributeName(attrNum) }}
          </h3>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                  Indicator
                </th>
                <th
                  v-for="company in selectedCompanies"
                  :key="company.id"
                  class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  <div>{{ company.company_name }}</div>
                  <div class="text-xs font-normal text-gray-400 mt-1">({{ company.symbol }})</div>
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="indicator in indicators"
                :key="indicator.code"
                class="hover:bg-gray-50"
              >
                <td class="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white z-10">
                  <div>
                    <p class="font-semibold">{{ indicator.name }}</p>
                    <p class="text-xs text-gray-500 mt-1">{{ indicator.code }}</p>
                    <span
                      class="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded"
                      :class="getPillarClass(indicator.pillar)"
                    >
                      {{ indicator.pillar }}
                    </span>
                  </div>
                </td>
                <td
                  v-for="company in selectedCompanies"
                  :key="company.id"
                  class="px-6 py-4 text-sm text-center"
                  :class="getCellHighlightClass(indicator.code, company.id)"
                >
                  <div v-if="getIndicatorValue(indicator.code, company.id)">
                    <div class="font-semibold text-gray-900">
                      {{ formatValue(getIndicatorValue(indicator.code, company.id)) }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      {{ indicator.unit }}
                    </div>
                    <div class="flex items-center justify-center gap-1 mt-2">
                      <div
                        class="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden"
                        :title="`Confidence: ${(getIndicatorConfidence(indicator.code, company.id) * 100).toFixed(0)}%`"
                      >
                        <div
                          class="h-full rounded-full"
                          :class="getConfidenceBarClass(getIndicatorConfidence(indicator.code, company.id))"
                          :style="{ width: `${getIndicatorConfidence(indicator.code, company.id) * 100}%` }"
                        ></div>
                      </div>
                      <span class="text-xs text-gray-600">
                        {{ (getIndicatorConfidence(indicator.code, company.id) * 100).toFixed(0) }}%
                      </span>
                    </div>
                  </div>
                  <div v-else class="text-gray-400 italic">
                    N/A
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Industry Benchmarks (if available) -->
      <div v-if="industryBenchmarks.length > 0" class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Industry Benchmarks
        </h3>
        <p class="text-sm text-gray-600 mb-4">
          Average values across {{ industryName }} industry
        </p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="(benchmark, index) in industryBenchmarks"
            :key="index"
            class="border rounded-lg p-4"
          >
            <p class="text-sm font-medium text-gray-700 mb-1">{{ benchmark.name }}</p>
            <p class="text-2xl font-bold text-gray-900">{{ benchmark.average }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ benchmark.unit }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && selectedCompanies.length < 2" class="bg-white rounded-lg shadow-md p-12 text-center">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <p class="text-gray-600 text-lg mb-2">Select at least 2 companies to compare</p>
      <p class="text-gray-500 text-sm">Use the search box above to find and add companies</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useIndicatorStore } from '@/stores/indicatorStore'
import type { Company, ExtractedIndicator } from '@/types'

const companyStore = useCompanyStore()
const indicatorStore = useIndicatorStore()

// State
const searchQuery = ref('')
const searchResults = ref<Company[]>([])
const selectedCompanies = ref<Company[]>([])
const selectedYear = ref<number | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const comparisonData = ref<{
  companies: Company[]
  indicators: Record<number, ExtractedIndicator[]>
} | null>(null)

// Filters
const filterPillar = ref<'' | 'E' | 'S' | 'G'>('')
const filterAttribute = ref<number | ''>('')
const highlightDifferences = ref(true)

// Computed
const definitions = computed(() => indicatorStore.definitions)

const availableYears = computed(() => {
  const years = [2024, 2023, 2022, 2021, 2020]
  return years
})

const industryName = computed(() => {
  if (selectedCompanies.value.length === 0) return ''
  const industries = [...new Set(selectedCompanies.value.map(c => c.industry))]
  return industries.length === 1 ? industries[0] : 'Multiple Industries'
})

const industryBenchmarks = computed<Array<{
  indicator: string
  name: string
  average: string
  unit: string
}>>(() => {
  // Placeholder for industry benchmarks
  // In a real implementation, this would fetch from the API
  return []
})

const groupedIndicators = computed(() => {
  if (!comparisonData.value) return {}

  const grouped: Record<number, Array<{
    code: string
    name: string
    unit: string
    pillar: 'E' | 'S' | 'G'
    attribute: number
  }>> = {}

  // Get all unique indicators across all companies
  const allIndicators = new Set<number>()
  Object.values(comparisonData.value.indicators).forEach(indicators => {
    indicators.forEach(ind => allIndicators.add(ind.indicator_id))
  })

  // Group by attribute
  allIndicators.forEach(indicatorId => {
    const def = definitions.value.find(d => d.id === indicatorId)
    if (!def) return

    // Apply filters
    if (filterPillar.value && def.pillar !== filterPillar.value) return
    if (filterAttribute.value && def.attribute_number !== filterAttribute.value) return

    const attr = def.attribute_number
    if (!grouped[attr]) {
      grouped[attr] = []
    }

    grouped[attr].push({
      code: def.indicator_code,
      name: def.parameter_name,
      unit: def.measurement_unit || '',
      pillar: def.pillar,
      attribute: def.attribute_number
    })
  })

  // Sort indicators within each attribute
  Object.keys(grouped).forEach(attr => {
    grouped[parseInt(attr)].sort((a, b) => a.name.localeCompare(b.name))
  })

  return grouped
})

// BRSR Attribute Names
const attributeNames: Record<number, string> = {
  1: 'GHG Footprint',
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
const handleSearch = async () => {
  if (searchQuery.value.trim().length < 2) {
    searchResults.value = []
    return
  }

  try {
    const results = await companyStore.searchCompanies(searchQuery.value)
    searchResults.value = results
  } catch (err) {
    console.error('Search error:', err)
  }
}

const isCompanySelected = (companyId: number): boolean => {
  return selectedCompanies.value.some(c => c.id === companyId)
}

const addCompany = (company: Company) => {
  if (selectedCompanies.value.length >= 4) return
  if (isCompanySelected(company.id)) return

  selectedCompanies.value.push(company)
  searchQuery.value = ''
  searchResults.value = []
}

const removeCompany = (companyId: number) => {
  selectedCompanies.value = selectedCompanies.value.filter(c => c.id !== companyId)
  comparisonData.value = null
}

const loadComparison = async () => {
  if (selectedCompanies.value.length < 2 || !selectedYear.value) return

  loading.value = true
  error.value = null

  try {
    const companyIds = selectedCompanies.value.map(c => c.id)
    const data = await indicatorStore.compareIndicators(companyIds, selectedYear.value)
    comparisonData.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load comparison data'
    console.error('Comparison error:', err)
  } finally {
    loading.value = false
  }
}

const getIndicatorValue = (indicatorCode: string, companyId: number): ExtractedIndicator | null => {
  if (!comparisonData.value) return null

  const indicators = comparisonData.value.indicators[companyId] || []
  const def = definitions.value.find(d => d.indicator_code === indicatorCode)
  if (!def) return null

  return indicators.find(ind => ind.indicator_id === def.id) || null
}

const getIndicatorConfidence = (indicatorCode: string, companyId: number): number => {
  const indicator = getIndicatorValue(indicatorCode, companyId)
  return indicator?.confidence_score || 0
}

const formatValue = (indicator: ExtractedIndicator | null): string => {
  if (!indicator) return 'N/A'
  
  if (indicator.numeric_value !== null && indicator.numeric_value !== undefined) {
    return indicator.numeric_value.toLocaleString()
  }
  return indicator.extracted_value || 'N/A'
}

const getCellHighlightClass = (indicatorCode: string, companyId: number): string => {
  if (!highlightDifferences.value) return ''
  if (!comparisonData.value) return ''

  // Get all values for this indicator
  const values: number[] = []
  selectedCompanies.value.forEach(company => {
    const indicator = getIndicatorValue(indicatorCode, company.id)
    if (indicator?.numeric_value !== null && indicator?.numeric_value !== undefined) {
      values.push(indicator.numeric_value)
    }
  })

  if (values.length < 2) return ''

  const currentIndicator = getIndicatorValue(indicatorCode, companyId)
  if (!currentIndicator?.numeric_value) return ''

  const avg = values.reduce((a, b) => a + b, 0) / values.length
  const stdDev = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - avg, 2), 0) / values.length)

  // Highlight if value is more than 1 standard deviation from mean
  const diff = Math.abs(currentIndicator.numeric_value - avg)
  if (diff > stdDev) {
    return currentIndicator.numeric_value > avg ? 'bg-green-50' : 'bg-yellow-50'
  }

  return ''
}

const getAttributeName = (attrNum: number): string => {
  return attributeNames[attrNum] || `Attribute ${attrNum}`
}

const getPillarClass = (pillar: 'E' | 'S' | 'G'): string => {
  const classes: Record<string, string> = {
    E: 'bg-green-100 text-green-800',
    S: 'bg-blue-100 text-blue-800',
    G: 'bg-purple-100 text-purple-800'
  }
  return classes[pillar] || 'bg-gray-100 text-gray-800'
}

const getConfidenceBarClass = (confidence: number): string => {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.6) return 'bg-yellow-500'
  return 'bg-red-500'
}

const exportData = () => {
  if (!comparisonData.value) return

  // Build CSV content
  const rows: string[][] = []
  
  // Header row
  const header = ['Attribute', 'Indicator', 'Code', 'Unit', 'Pillar']
  selectedCompanies.value.forEach(company => {
    header.push(`${company.company_name} (${company.symbol})`)
    header.push('Confidence')
  })
  rows.push(header)

  // Data rows
  Object.entries(groupedIndicators.value).forEach(([attrNum, indicators]) => {
    indicators.forEach(indicator => {
      const row = [
        getAttributeName(parseInt(attrNum)),
        indicator.name,
        indicator.code,
        indicator.unit,
        indicator.pillar
      ]

      selectedCompanies.value.forEach(company => {
        const value = getIndicatorValue(indicator.code, company.id)
        row.push(formatValue(value))
        row.push(value ? `${(value.confidence_score * 100).toFixed(0)}%` : 'N/A')
      })

      rows.push(row)
    })
  })

  // Convert to CSV
  const csv = rows.map(row => 
    row.map(cell => `"${cell}"`).join(',')
  ).join('\n')

  // Download
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `company-comparison-${selectedYear.value}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// Lifecycle
onMounted(async () => {
  // Load indicator definitions if not already loaded
  if (definitions.value.length === 0) {
    await indicatorStore.fetchDefinitions()
  }
})
</script>

<style scoped>
/* Sticky column styling */
.sticky {
  position: sticky;
}

/* Smooth transitions */
.transition {
  transition: all 0.2s ease-in-out;
}
</style>
