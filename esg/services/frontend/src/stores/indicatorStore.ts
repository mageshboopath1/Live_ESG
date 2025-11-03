import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ExtractedIndicator, BRSRIndicatorDefinition, Citation } from '@/types'
import apiClient from '@/services/api'

interface IndicatorCache {
  [key: string]: {
    data: ExtractedIndicator[]
    timestamp: number
  }
}

interface DefinitionCache {
  data: BRSRIndicatorDefinition[]
  timestamp: number
}

interface IndicatorDetailsCache {
  [indicatorId: number]: {
    indicator: ExtractedIndicator
    definition: BRSRIndicatorDefinition
    citations: Citation[]
    timestamp: number
  }
}

const CACHE_TTL = 60 * 60 * 1000 // 1 hour in milliseconds
const DEFINITION_CACHE_TTL = 24 * 60 * 60 * 1000 // 24 hours for definitions

export const useIndicatorStore = defineStore('indicator', () => {
  // State
  const indicators = ref<ExtractedIndicator[]>([])
  const definitions = ref<BRSRIndicatorDefinition[]>([])
  const selectedIndicator = ref<ExtractedIndicator | null>(null)
  const selectedDefinition = ref<BRSRIndicatorDefinition | null>(null)
  const citations = ref<Citation[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Cache
  const indicatorCache = ref<IndicatorCache>({})
  const definitionCache = ref<DefinitionCache | null>(null)
  const indicatorDetailsCache = ref<IndicatorDetailsCache>({})

  // Computed
  const indicatorsByAttribute = computed(() => {
    const grouped: Record<number, ExtractedIndicator[]> = {}
    indicators.value.forEach((indicator) => {
      const def = definitions.value.find((d) => d.id === indicator.indicator_id)
      if (def) {
        const attr = def.attribute_number
        if (!grouped[attr]) {
          grouped[attr] = []
        }
        grouped[attr].push(indicator)
      }
    })
    return grouped
  })

  const indicatorsByPillar = computed(() => {
    const grouped: Record<'E' | 'S' | 'G', ExtractedIndicator[]> = {
      E: [],
      S: [],
      G: []
    }
    indicators.value.forEach((indicator) => {
      const def = definitions.value.find((d) => d.id === indicator.indicator_id)
      if (def) {
        grouped[def.pillar].push(indicator)
      }
    })
    return grouped
  })

  const validIndicators = computed(() => {
    return indicators.value.filter((i) => i.validation_status === 'valid')
  })

  const highConfidenceIndicators = computed(() => {
    return indicators.value.filter((i) => i.confidence_score >= 0.8)
  })

  // Helper: Check if cache is valid
  const isCacheValid = (timestamp: number, ttl = CACHE_TTL): boolean => {
    return Date.now() - timestamp < ttl
  }

  // Actions
  const fetchDefinitions = async (forceRefresh = false) => {
    // Check cache first
    if (!forceRefresh && definitionCache.value && isCacheValid(definitionCache.value.timestamp, DEFINITION_CACHE_TTL)) {
      definitions.value = definitionCache.value.data
      return definitionCache.value.data
    }

    loading.value = true
    error.value = null

    try {
      const defs = await apiClient.getBRSRIndicatorDefinitions()
      definitions.value = defs
      
      // Update cache
      definitionCache.value = {
        data: defs,
        timestamp: Date.now()
      }

      return defs
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch indicator definitions'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCompanyIndicators = async (
    companyId: number,
    year: number,
    params?: { attribute?: number; pillar?: 'E' | 'S' | 'G' },
    forceRefresh = false
  ) => {
    const cacheKey = `${companyId}-${year}-${params?.attribute || 'all'}-${params?.pillar || 'all'}`
    
    // Check cache first
    const cached = indicatorCache.value[cacheKey]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      indicators.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const companyIndicators = await apiClient.getCompanyIndicators(companyId, year, params)
      indicators.value = companyIndicators
      
      // Update cache
      indicatorCache.value[cacheKey] = {
        data: companyIndicators,
        timestamp: Date.now()
      }

      return companyIndicators
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch indicators'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchIndicatorDetails = async (indicatorId: number, forceRefresh = false) => {
    // Check cache first
    const cached = indicatorDetailsCache.value[indicatorId]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      selectedIndicator.value = cached.indicator
      selectedDefinition.value = cached.definition
      citations.value = cached.citations
      return cached
    }

    loading.value = true
    error.value = null

    try {
      const details = await apiClient.getIndicator(indicatorId)
      selectedIndicator.value = details.indicator
      selectedDefinition.value = details.definition
      citations.value = details.citations
      
      // Update cache
      indicatorDetailsCache.value[indicatorId] = {
        ...details,
        timestamp: Date.now()
      }

      return details
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch indicator details'
      throw err
    } finally {
      loading.value = false
    }
  }

  const compareIndicators = async (
    companyIds: number[],
    year: number,
    indicatorCode?: string
  ) => {
    loading.value = true
    error.value = null

    try {
      const comparison = await apiClient.compareIndicators(companyIds, year, indicatorCode)
      return comparison
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to compare indicators'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCitations = async (extractedIndicatorId: number) => {
    loading.value = true
    error.value = null

    try {
      const citationData = await apiClient.getCitations(extractedIndicatorId)
      citations.value = citationData
      return citationData
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch citations'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getDefinitionByCode = (code: string): BRSRIndicatorDefinition | undefined => {
    return definitions.value.find((d) => d.indicator_code === code)
  }

  const getDefinitionById = (id: number): BRSRIndicatorDefinition | undefined => {
    return definitions.value.find((d) => d.id === id)
  }

  const clearCache = () => {
    indicatorCache.value = {}
    definitionCache.value = null
    indicatorDetailsCache.value = {}
  }

  const clearError = () => {
    error.value = null
  }

  const clearSelection = () => {
    selectedIndicator.value = null
    selectedDefinition.value = null
    citations.value = []
  }

  return {
    // State
    indicators,
    definitions,
    selectedIndicator,
    selectedDefinition,
    citations,
    loading,
    error,
    
    // Computed
    indicatorsByAttribute,
    indicatorsByPillar,
    validIndicators,
    highConfidenceIndicators,
    
    // Actions
    fetchDefinitions,
    fetchCompanyIndicators,
    fetchIndicatorDetails,
    compareIndicators,
    fetchCitations,
    getDefinitionByCode,
    getDefinitionById,
    clearCache,
    clearError,
    clearSelection
  }
})
